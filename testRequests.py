#!/usr/bin/env python

################################
#
# testRequests.py
#
#  Script to test the time and size per event of
#  requests in McM. Prepares results in a CSV file
#  that can be used by manageRequests.py
#
#  author: David G. Sheffield (Rutgers)
#
################################

import sys
import os, shutil
import subprocess
import argparse
import csv
import re
import datetime
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM
from requestClass import * # Load class to store request information

def getArguments():
    parser = argparse.ArgumentParser(description='Test McM requests.')

    # Command line flags
    parser.add_argument('-i', '--ids', dest='ids', help=
                        'List of PrepIDs to be tested. Separate range by >.')
    parser.add_argument('-f', '--file', dest='csv', help='Input CSV file.')
    parser.add_argument('-newcsv', action='store_true', dest='newcsv',
                        help="Don't overwrite testRequest.csv")
    parser.add_argument('-o', '--output', dest='output', default='testRequest.csv',
                        help='Output CSV file')
    parser.add_argument('-n', dest='nEvents', help='Number of events to test.')
    parser.add_argument('-nxsec', dest='nEventsXsec', default=1500, help='Number of events to test for Cross section purpose.')
    parser.add_argument('-qxsec', dest='xsecQueue', default='8nh', help='Submission queue for Cross section test.')
    parser.add_argument('-xsec', action='store_true', dest='xsec',
                        help='Run another parallel batch job with GEN step only and not SIM (useful to get cross section).')

    args_ = parser.parse_args()
    return args_

def fillIDRange(pwg, campaign, first, last):
    first = int(first)
    last = int(last)
    requests = []
    if first > last:
        print "Error: PrepID range out of order. {0}-{1}-{2:05d} > {0}-{1}-{3:05d}".format(
            pwg, campaign, first, last)
        sys.exit(4)

    for number in range(first, last+1):
        tmpReq = Request()
        tmpReq.setPrepId("{0}-{1}-{2:05d}".format(pwg, campaign, number))
        requests.append(tmpReq)
    return requests

def parseIDList(compactList):
    splitList = compactList.split(',')
    requests = []
    for subList in splitList:
        splitSubList = subList.split('-')
        if len(splitSubList) == 3:
            tmpReq = Request()
            tmpReq.setPrepId(subList)
            requests.append(tmpReq)
        elif len(splitSubList) == 4:
            requests = requests + fillIDRange(splitSubList[0], splitSubList[1],
                                              splitSubList[2], splitSubList[3])
        elif len(splitSubList) == 6:
            if splitSubList[0] != splitSubList[3]:
                print "Error: PrepID range must be for the same PWG."
                sys.exit(4)
            if splitSubList[1] != splitSubList[4]:
                print "Error: PrepID range must be for the same campaign."
                sys.exit(4)
            requests = requests + fillIDRange(splitSubList[0], splitSubList[1],
                                              splitSubList[2], splitSubList[5])
        else:
            print "Error: Poorly formed PrepID list."
            print "Exiting with status 3."
            sys.exit(3)
    return requests

def getTestScript(PrepID, nEvents, xsec):
    request_type = "requests"
    if "chain_" in PrepID:
        request_type = "chained_requests"

    get_test = ""
    if nEvents is None:
        get_test =  "curl -s --insecure \
https://cms-pdmv.cern.ch/mcm/public/restapi/{0}/get_test/{1} -o {2}.sh".format(
            request_type, PrepID, PrepID)
    else:
        # add "/N" to end of URL to get N events
        get_test =  "curl -s --insecure \
https://cms-pdmv.cern.ch/mcm/public/restapi/{0}/get_test/{1}/{2} -o {3}.sh".format(
            request_type, PrepID, nEvents, PrepID)
    print get_test
    subprocess.call(get_test, shell=True)

    if (request_type == "chained_requests" and (nEvents is not None or xsec)) or xsec:
        filename = "{0}.sh".format(PrepID)
        if xsec:
            shutil.copy2(filename, filename.replace('.sh','_xsec.sh'))
            filename = filename.replace('.sh','_xsec.sh')
        
        tmpfilename = "tmp{0}.sh".format(PrepID)
        inputfile = open(filename, 'r')
        outputfile = open(tmpfilename, 'w')
        for line in inputfile:
            if nEvents is not None:
                outline = re.sub('(.*--eventcontent LHE.*-n) \d*( .*)',
                                 r'\1 {0}\2'.format(nEvents), line)
                outline = re.sub('(.*--eventcontent DQM.*-n) \d*( .*)',
                                 r'\1 {0}\2'.format(nEvents), outline)
                outline = re.sub('(.*--eventcontent RAWSIM.*-n) \d*( .*)',
                                 r'\1 {0}\2'.format(nEvents), outline)
            if xsec:
                outline = line.replace('GEN,SIM','GEN')
                
            outputfile.write(outline)
            
        inputfile.close()
        outputfile.close()
        os.rename(tmpfilename, filename)

    subprocess.call("chmod 755 {0}.sh".format(PrepID), shell=True)
    if xsec:
        subprocess.call("chmod 755 {0}_xsec.sh".format(PrepID), shell=True)

    return

def submitToBatch(PrepId, xsec, xsecQueue):
    if xsec:
        batch_command = "bsub -q "+xsecQueue+" {0}_xsec.sh".format(PrepId)
    else:
        batch_command = "bsub -q 8nh {0}.sh".format(PrepId)
    output = subprocess.Popen(batch_command, stdout=subprocess.PIPE,
                              shell=True).communicate()[0]
    match = re.match('Job <(\d*)> is', output)
    jobID = match.group(1)
    # jobID = '735510839'
    # if xsec: jobID = '735510837'
    print batch_command,' (jobID= '+jobID+')'
    return jobID

def createTest(compactPrepIDList, outputFile, newcsv, nEvents, xsec, nEventsXsec, xsecQueue):
    requests = parseIDList(compactPrepIDList)

    if os.path.isfile(outputFile) and newcsv:
      add_datetime = str(datetime.datetime.now()).replace(' ','_').replace(':','-').split('.')[0]
      outputFile = outputFile.replace('.csv','')+'_'+add_datetime+'.csv'
    csvfile = csv.writer(open(outputFile, 'w'))
    row = ['PrepId', 'JobId', 'Time per event [s]', 'Size per event [kB]']
    # if xsec:
    row = row + ['JobId xsec','Cross section [pb]','Filter efficiency','Filter efficiency error','Match efficiency','Match efficiency error']
    csvfile.writerow(row)

    print "Testing {0} requests".format(len(requests))
    for req in requests:
        # if xsec: # and 'GS' in req.getPrepId():
        getTestScript(req.getPrepId(), nEventsXsec,True)
        jobIDxsec = submitToBatch(req.getPrepId(),True,xsecQueue)
        req.setJobIDxsec(jobIDxsec)
        
        getTestScript(req.getPrepId(), nEvents,False)
        jobID = submitToBatch(req.getPrepId(),False,'8nh')
        req.setJobID(jobID)
        
        searched = re.search('chain_', req.getPrepId())
        if searched is None:
            # if xsec:
            csvfile.writerow([req.getPrepId(), req.getJobID(),"1","1",req.getJobIDxsec(),"1","1","0.1","1","0.1"])
            # else:
                # csvfile.writerow([req.getPrepId(), req.getJobID(), "", ""])
        else:
            mcm = restful(dev=False) # Get McM connection
            mcm_req = mcm.getA('chained_requests', req.getPrepId())
            wmLHEPrepId = mcm_req['chain'][0]
            GSPrepId = mcm_req['chain'][1]
            # if xsec:
            csvfile.writerow([wmLHEPrepId, req.getJobID(), "1", "1", req.getJobIDxsec(), "1","1","0.1","1","0.1"])
            csvfile.writerow([GSPrepId, req.getJobID(), "1", "1", req.getJobIDxsec(), "1","1","0.1","1","0.1"])
            # else:
                # csvfile.writerow([wmLHEPrepId, req.getJobID(), "", ""])
                # csvfile.writerow([GSPrepId, req.getJobID(), "", ""])
    return

def exitDuplicateField(file_in_,field_):
    print "Error: File {0} contains multiple instances of the field {1}".format(
        file_in_, field_)
    sys.exit(5)

def getFields(csvfile):
    # List of indices for each field in CSV file
    list = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
             -1, -1, -1, -1,-1]
    header = csv.reader(csvfile).next()
    for ind, field in enumerate(header):
        if field in ['Dataset name', 'Dataset Name', 'Dataset', 'dataset']:
            #ensure no duplicate fields
            if list[0] > -1:
                exitDuplicateField(file_in_, "Dataset name")
            list[0] = ind
        elif field in ['EOS', 'eos', 'Eos', 'MCDBID', 'mcdbid']:
            if list[1] > -1:
                exitDuplicateField(file_in_, "EOS")
            list[1] = ind
        elif field in ['Cross section [pb]', 'Cross section',
                       'Cross section (pb)', 'Cross Section',
                       'Cross Section [pb]', 'Cross Section (pb)', 'CS',
                       'CS [pb]', 'CS (pb)', 'Xsec', 'Xsec [pb]', 'Xsec (pb)']:
            if list[2] > -1:
                exitDuplicateField(file_in_, "Cross section")
            list[2] = ind
        elif field in ['Total events', 'Total Events', 'Events', 'events',
                       'total events', 'Number of Events']:
            if list[3] > -1:
                exitDuplicateField(file_in_, "Total events")
            list[3] = ind
        elif field in ['Fragment name', 'Fragment Name',
                       'Generator fragment name', 'Generator Fragment Name',
                       'Fragment', 'fragment']:
            if list[4] > -1:
                exitDuplicateField(file_in_, "Fragment name")
            list[4] = ind
        elif field in ['Time per event [s]', 'Time per event',
                       'Time per event (s)', 'Time per Event',
                       'Time per Event [s]', 'Time per Event (s)', 'Time',
                       'Time [s]', 'Time (s)', 'time', 'time [s]', 'time (s)']:
            if list[5] > -1:
                exitDuplicateField(file_in_, "Time per event [s]")
            list[5] = ind
        elif field in ['Size per event [kB]', 'Size per event',
                       'Size per event (kB)', 'Size per Event',
                       'Size per Event [kB]', 'Size per Event (kB)',
                       'size', 'size [kB]', 'size (kB)']:
            if list[6] > -1:
                exitDuplicateField(file_in_, "Size per event [kB]")
            list[6] = ind
        elif field in ['Tag', 'tag', 'Fragment Tag', 'Fragment tag',
                       'fragment tag', 'sha', 'SHA', 'SHA-1', 'sha-1']:
            if list[7] > -1:
                exitDuplicateField(file_in_, "Fragment tag")
            list[7] = ind
        elif field in ['Generator', 'generator']:
            if list[8] > -1:
                exitDuplicateField(file_in_, "Generator")
            list[8] = ind
        elif field in ['Filter efficiency', 'FilterEfficiency',
                       'filter efficiency']:
            if list[9] > -1:
                exitDuplicateField(file_in_, "Filter efficiency")
            list[9] = ind
        elif field in ['Filter efficiency error', 'Filter Efficiency Error',
                       'filter efficiency error']:
            if list[10] > -1:
                exitDuplicateField(file_in_, "Filter efficiency error")
            list[10] = ind
        elif field in ['Match efficiency', 'Match Efficiency',
                       'match efficiency']:
            if list[11] > -1:
                exitDuplicateField(file_in_, "Match efficiency")
            list[11] = ind
        elif field in ['Match efficiency error', 'Match Efficiency Error',
                       'match efficiency error']:
            if list[12] > -1:
                exitDuplicateField(file_in_, "Match efficiency error")
            list[12] = ind
        elif field in ['PWG', 'pwg']:
            if list[13] > -1:
                exitDuplicateField(file_in_, "PWG")
            list[13] = ind
        elif field in ['Campaign', 'campaign', 'Member of Campaign',
                       'Member of campaign', 'member of campaign']:
            if list[14] > -1:
                exitDuplicateField(file_in_, "Member of campaign")
            list[14] = ind
        elif field in ['PrepId', 'PrepID', 'PREPID', 'prepid']:
            if list[15] > -1:
                exitDuplicateField(file_in_, "PrepId")
            list[15] = ind
        elif field in ['Sequences customise', 'Sequences customize']:
            if list[16] > -1:
                exitDuplicateField(file_in_, "Sequences customise")
            list[16] = ind
        elif field in ['Process string', 'Process String']:
            if list[17] > -1:
                exitDuplicateField(file_in_, "Process string")
            list[17] = ind
        elif field in ['Gridpack location', 'Gridpack']:
            if list[18] > -1:
                exitDuplicateField(file_in_, "Gridpack location")
            list[18] = ind
        elif field in ['Gridpack cards URL', 'Cards URL',
                       'Gridpack cards location', 'Cards location']:
            if list[19] > -1:
                exitDuplicateField(file_in_, "Gridpack cards URL")
            list[19] = ind
        elif field in ['JobId']:
            if list[20] > -1:
                exitDuplicateField(file_in_, "JobId")
            list[20] = ind
        elif field in ['JobId xsec']:
            if list[21] > -1:
                exitDuplicateField(file_in_, "JobId xsec")
            list[21] = ind
        elif field in ['Local gridpack location', 'Local LHE', 'LHE']:
            continue
        else:
            print "Error: The field {0} is not valid.".format(field)
            sys.exit(6)

    return list

def fillFields(csvfile, fields):
    requests = [] # List containing request objects
    num_requests = 0
    for row in csv.reader(csvfile):
        num_requests += 1
        tmpReq = Request()
        if fields[0] > -1:
            tmpReq.setDataSetName(row[fields[0]])
        if fields[1] > -1:
            tmpReq.setMCDBID(row[fields[1]])
        if fields[2] > -1 and row[fields[2]] != "" and float(row[fields[2]]) != 1:
            tmpReq.setCS(row[fields[2]])
        if fields[3] > -1:
            tmpReq.setEvts(row[fields[3]])
        if fields[14] > -1:
            campaign = row[fields[14]]
            tmpReq.setCamp(campaign)
        if fields[4] > -1:
            tmpReq.setFrag(formatFragment(row[fields[4]],campaign))
        if fields[5] > -1 and row[fields[5]] != "" and float(row[fields[5]]) != 1:
            tmpReq.setTime(row[fields[5]])
        if fields[6] > -1 and row[fields[6]] != "" and float(row[fields[6]]) != 1:
            tmpReq.setSize(row[fields[6]])
        if fields[7] > -1:
            tmpReq.setTag(row[fields[7]])
        if fields[8] > -1:
            tmpReq.setGen(row[fields[8]].split(" ")) # Multiple generators separated by spaces
        if fields[9] > -1  and row[fields[9]] != "" and float(row[fields[9]]) != 1:
            tmpReq.setFiltEff(row[fields[9]])
        if fields[10] > -1:
            tmpReq.setFiltEffErr(row[fields[10]])
        if fields[11] > -1 and row[fields[11]] != "" and float(row[fields[11]]) != 1:
            tmpReq.setMatchEff(row[fields[11]])
        if fields[12] > -1:
            tmpReq.setMatchEffErr(row[fields[12]])
        if fields[13] > -1:
            tmpReq.setPWG(row[fields[13]])
        if fields[15] > -1:
            tmpReq.setPrepId(row[fields[15]])
        if fields[16] > -1:
            tmpReq.setSequencesCustomise(row[fields[16]])
        if fields[17] > -1:
            tmpReq.setProcessString(row[fields[17]])
        if fields[18] > -1:
            if fields[19] > -1:
                tmpReq.setMcMFrag(createLHEProducer(row[fields[18]],
                                                    row[fields[19]]))
            else:
                tmpReq.setMcMFrag(createLHEProducer(row[fields[18]], ""))
        if fields[20] > -1:
            tmpReq.setJobID(row[fields[20]])
        if fields[21] > -1:
            tmpReq.setJobIDxsec(row[fields[21]])
        requests.append(tmpReq)
    return requests, num_requests

def rewriteCSVFile(csvfile, requests):
    csvWriter = csv.writer(csvfile)
    requests_number=0
    for req in requests:
        if requests_number == 0:
            row = ['PrepId', 'JobId', 'Time per event [s]', 'Size per event [kB]']
            row = row + ['JobId xsec','Cross section [pb]','Filter efficiency','Filter efficiency error','Match efficiency','Match efficiency error']
            csvWriter.writerow(row)
        
        timePerEvent = 1
        if req.useTime(): timePerEvent = req.getTime()
        sizePerEvent = 1
        if req.useSize(): sizePerEvent = req.getSize()
        CS = 1
        if req.useCS(): CS = req.getCS()
        FiltEff = 1
        if req.useFiltEff(): FiltEff = req.getFiltEff()
        MatchEff = 1
        if req.useMatchEff(): MatchEff = req.getMatchEff()
        
        csvWriter.writerow([req.getPrepId(), 
                            req.getJobID(), 
                            timePerEvent,
                            sizePerEvent, 
                            req.getJobIDxsec(), 
                            CS,
                            FiltEff,
                            req.getFiltEffErr(), 
                            MatchEff,
                            req.getMatchEffErr(), 
                            ])
        # else:
            # csvWriter.writerow([req.getPrepId(), req.getJobID(), req.getJobIDxsec(), timePerEvent,
                            # sizePerEvent])
        requests_number = requests_number+1
    return

def getTimeSizeFromFile(stdoutFile, iswmLHE):
    totalSize = 0
    timePerEvent = 0
    nEvents = 0
    fileContents = open(stdoutFile, 'r')
    for line in fileContents:
        match = re.match('<TotalEvents>(\d*)</TotalEvents>', line)
        if match is not None:
            nEvents = float(match.group(1))
            continue
        # match = re.match('    <Metric Name="Timing-tstoragefile-write-totalMegabytes" Value="(\d*\.\d*)"/>',
                         # line)
        # if match is not None:
            # totalSize = float(match.group(1))
            # continue
        if 'McM Size/event: ' in line:
            totalSize = float(line.replace('McM Size/event: ',''))
            # print 'size/event',totalSize
            continue
        # match = re.match('    <Metric Name="AvgEventTime" Value="(\d*\.\d*)"/>',
                         # line)
        # if match is not None:
            # timePerEvent = float(match.group(1))
            # if iswmLHE: break
            # else: continue
        if 'McM time_event value:' in line:
            timePerEvent = float(line.replace('McM time_event value: ',''))
            # print 'time/event',timePerEvent
            if iswmLHE: break
            else: continue

    if nEvents != 0:
        # sizePerEvent = totalSize*1024.0/nEvents
        sizePerEvent = totalSize
    else:
        sizePerEvent = -1
    return timePerEvent, sizePerEvent

def getCSMatchFiltEffFromFile(stdoutFile, iswmLHE):
    MatchEff = 1; HepMCFiltEff = 1; FiltEff = 1; CS = 0; 
    matchMatchEff = ''; matchFiltEff = ''; matchCS = ''; 
    fileContents = open(stdoutFile, 'r')
    for line in fileContents:
        # if 'Total		' in line and '+/-' in line: 
            # MatchEff = float(line.split()[16])/100.
        if 'Matching efficiency = ' in line:
            line = line.replace('Matching efficiency = ','').split('+/-')[0]
            # print line
            MatchEff = float(line)
            # print 'MatchEff',MatchEff
            continue
        # if 'Filter efficiency (event-level)= ' in line: 
            # FiltEff = float(line.split()[7])
        if 'Filter efficiency (event-level)= ' in line: 
            line = line.split('=')[2].split('+-')[0]
            # print line
            FiltEff = float(line)
            # print 'FiltEff',FiltEff
            continue
        if 'After filter: final cross section' in line: 
            CS = float(line.split('=')[1].split('+-')[0].replace(' ',''))
            if iswmLHE: break
            else: continue
    # sys.exit(1)
    return MatchEff , FiltEff , CS

def getTimeSize(requests):
    number_complete = 0
    for req in requests:
        if not req.useTime() or not req.useSize():
            stdoutFile = "LSFJOB_{0}/STDOUT".format(req.getJobID())
            if os.path.exists(stdoutFile):
                number_complete += 1
                iswmLHE = False
                searched = re.search('wmLHE', req.getPrepId())
                if searched is not None:
                    iswmLHE = True
                timePerEvent, sizePerEvent = getTimeSizeFromFile(stdoutFile,
                                                                 iswmLHE)
                
                # print 'timePerEvent',timePerEvent,'sizePerEvent',sizePerEvent
                req.setTime(timePerEvent)
                req.setSize(sizePerEvent)
        else:
            number_complete += 1

    if number_complete == len(requests):
        print "Extracted Time and Size per event for all {0} requests.".format(len(requests))
    else:
        print "Extracted Time and Size per event for {0} of {1} requests. {2} requests remain.".format(
            number_complete, len(requests), len(requests) - number_complete)
    return

def getxSecMatchFiltEff(requests):
    number_complete = 0
    for req in requests:
        if not req.useCS() or not req.useFiltEff() or not req.useMatchEff():
            stdoutFile = "LSFJOB_{0}/STDOUT".format(req.getJobIDxsec())
            # print 'stdoutFile', stdoutFile
            if os.path.exists(stdoutFile):
                number_complete += 1
                iswmLHE = False
                # searched = re.search('wmLHE', req.getPrepId())
                # if searched is not None:
                    # iswmLHE = True
                iswmLHE = 'wmLHE' in req.getPrepId() and not 'wmLHEGS' in req.getPrepId()
                if iswmLHE == False:
                    MatchEff, FiltEff, CSPerEvent = getCSMatchFiltEffFromFile(stdoutFile,iswmLHE)
                    req.setFiltEff(FiltEff)
                    req.setMatchEff(MatchEff)
                    req.setCS(CSPerEvent)
        else:
            number_complete += 1

    if number_complete == len(requests):
        print "Extracted Cross section for all {0} requests.".format(len(requests))
    else:
        print "Extracted Cross section for {0} of {1} requests. {2} requests remain.".format(
            number_complete, len(requests), len(requests) - number_complete)
    return

def extractTest(csvFile):
    csvfile = open(csvFile, 'r') # Open CSV file
    fields = getFields(csvfile)  # Get list of field indices
    # Fill list of request objects from CSV file and get number of requests
    requests, num_requests = fillFields(csvfile, fields)
    csvfile.close()

    getTimeSize(requests)
    getxSecMatchFiltEff(requests)
    
    csvfile = open(csvFile, 'w')
    rewriteCSVFile(csvfile, requests)

    return

def main():
    args = getArguments() # Setup flags and get arguments
    # print 'args.ids',args.ids,'args.csv',args.csv
    # sys.exit(1)
    if args.ids and args.csv:
        print "Error: Cannot use both -i and -f."
        sys.exit(1)
    elif args.ids:
        createTest(args.ids, args.output, args.newcsv, args.nEvents, args.xsec, args.nEventsXsec, args.xsecQueue)
    elif args.csv:
        extractTest(args.csv)
    else:
        print "Error: Must use either -i or -f."
        sys.exit(2)

if __name__ == '__main__':
    main()
