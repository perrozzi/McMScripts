#!/usr/bin/env python

################################
#
# getRequests.py
#
#  Script to get a list of requests from McM
#
#  author: David G. Sheffield (Rutgers)
#
################################

import sys
import os.path
import argparse
import csv
import pprint
import time
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM
from requestClass import * # Load class to store request information

class bcolors:
    MAGENTA = '\033[35m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    # RED = '\033[31m'
    YELLOW = '\033[33m'
    WHITE = '\033[1;37m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    Gray_like_Ghost = '\033[1;30m'
    RED = '\033[1;31m' 
    Green_like_Grass = '\033[1;32m' 
    Yellow_like_Yolk = '\033[1;33m'
    Blue_like_Blood = '\033[1;34m'
    Magenta_like_Mimosa = '\033[1;35m'
    CYAN = '\033[1;36m'
    Crimson_like_Chianti = '\033[1;38m'
    Highlighted_Red_like_Radish = '\033[1;41m'
    Highlighted_Green_like_Grass = '\033[1;42m'
    Highlighted_Brown_like_Bear = '\033[1;43m'
    Highlighted_Blue_like_Blood = '\033[1;44m'
    Highlighted_Magenta_like_Mimosa = '\033[1;45m'
    Highlighted_Cyan_like_Caribbean = '\033[1;46m'
    Highlighted_Gray_like_Ghost = '\033[1;47m'
    Highlighted_Crimson_like_Chianti = '\033[1;48m'

def getArguments():
    parser = argparse.ArgumentParser(
        description='Get a list of PrepIDs from McM based on a query.')

    # Command line flags
    parser.add_argument('query')
    parser.add_argument('-n', action='store_true', dest='getNew',
                        help='Only get requests with unmodified time and size per event.')
    parser.add_argument('-v', action='store_true', dest='getForValidation',
                        help='Only get requests with positive time and size per event.')
    parser.add_argument('-c', action='store_true', dest='getChain',
                        help='Return PrepID of chain.')
    parser.add_argument('-f', dest='format', type=int, default=0,
                        help='Format of output. 0 (default) = input for scripts, 1 = human-readable, 2 = HTML')
    parser.add_argument('-listattr', dest='listAttr', type=int, default=-1, 
                        help='List attributes for each PrepID. 0 (default) to 5 in increasing level of verbosity')

    args_ = parser.parse_args()
    return args_


def checkFile(file_):
    # Check that CSV file exists
    if not os.path.isfile(file_):
        print "Error: File {0} does not exist.".format(file_)
        sys.exit(1)


def getMcMlist(query_string,printout):
    useDev = False
    mcm = McM( dev=useDev ) # Get McM connection
    req_list = mcm.get('requests', query=query_string)
    return req_list

def getPrepIDListWithAttributes(query_string,listAttr):
    if listAttr < 7: 
      print 'MCM query string: ' + bcolors.MAGENTA + query_string + bcolors.ENDC
    temp = sys.stdout
    f = open('/dev/null', 'w')
    sys.stdout = f
    req_list = getMcMlist(query_string,True)
    sys.stdout = temp
    if req_list is None:
      print "\033[1;31mCould not get requests from McM\033[1;m"; sys.exit(1)

    if listAttr > 1 and listAttr < 7: print '\n======================================================================================================================================================================\n'
    if listAttr == 7: print 'prepid, dataset_name, extension, completed_events, total_events, cross_section'
    for req in req_list:
        if listAttr == 6: # full dump of the request object, useful for debugging purpose
            print bcolors.MAGENTA +\
                  'prepid='+ bcolors.ENDC,req['prepid'],\
                  ''+ bcolors.ENDC
            print str(req).replace("u'","'")
            print ''
        else:
            # print '======================================================================================================================================================================\n',\
                  # '======================================================================================================================================================================'
            if listAttr == 7:
              print req['prepid'],',', req['dataset_name'],
              if not 'DELETE' in req['dataset_name'] and (len(req['generator_parameters'])>0 and len(req['generator_parameters'][len(req['generator_parameters'])-1])>0): 
                print ',',req['extension'],',',req['completed_events'],',',req['total_events'],
                if(len(req['generator_parameters'])>0 and len(req['generator_parameters'][len(req['generator_parameters'])-1])>0): print ',',req['generator_parameters'][len(req['generator_parameters'])-1]['cross_section']
                else: print ''
              else: print ''
            else:
              if listAttr < 6: print bcolors.MAGENTA +\
                    'prepid='+ bcolors.ENDC,req['prepid'],', ',
              if listAttr < 8:
                print bcolors.MAGENTA+'Dataset name='+ bcolors.ENDC,req['dataset_name'],\
                    ', '+bcolors.MAGENTA+'Extension='+ bcolors.ENDC,req['extension'],
              else:
                print 'Dataset name=',req['dataset_name'],\
                    ', '+'Extension=',req['extension'],
              if listAttr < 6: print', '+bcolors.MAGENTA+'Completed/Total events='+ bcolors.ENDC,str(req['completed_events'])+'/'+str(req['total_events']),\
                    ''+ bcolors.ENDC,
              else: 
                  print '\t('+req['prepid']+')'
                  if listAttr < 8: print '\n'
                
              if listAttr > 0 and listAttr < 6:
                  print bcolors.RED +\
                        '\nApproval='+ bcolors.ENDC,req['approval'],\
                        ', '+bcolors.RED+'Status='+ bcolors.ENDC,req['status'],\
                        ', '+bcolors.RED+'Time Event='+ bcolors.ENDC,req['time_event'],\
                        ', '+bcolors.RED+'CMSSW Release='+ bcolors.ENDC,req['cmssw_release'],\
                        ', '+bcolors.RED+'Priority='+ bcolors.ENDC,req['priority'],\
                        ''+ bcolors.ENDC
              if listAttr == 0:
                  if(len(req['generator_parameters'])>0 and len(req['generator_parameters'][0])>0):
                      print bcolors.GREEN +\
                          'Cross Section='+ bcolors.ENDC,req['generator_parameters'][0]['cross_section'],'pb'+ bcolors.ENDC
              elif listAttr > 1 and listAttr < 6:
                  if(len(req['generator_parameters'])>0 and len(req['generator_parameters'][0])>0):
                      print bcolors.GREEN +\
                          'Cross Section='+ bcolors.ENDC,req['generator_parameters'][0]['cross_section'],'pb',\
                          ', '+bcolors.GREEN+'Filter efficiency='+ bcolors.ENDC,str(req['generator_parameters'][0]['filter_efficiency'])+' +/- '+str(req['generator_parameters'][0]['filter_efficiency_error']),\
                          ', '+bcolors.GREEN+'Match efficiency='+ bcolors.ENDC,str(req['generator_parameters'][0]['match_efficiency'])+' +/- '+str(req['generator_parameters'][0]['match_efficiency_error']),\
                          ''+ bcolors.ENDC
                  else:
                      print bcolors.GREEN +\
                          'Cross Section= -1 pb',\
                          ', Filter efficiency= -1',\
                          ', Match efficiency= -1',\
                          ''+ bcolors.ENDC
                  print bcolors.CYAN +\
                        'Tags='+ bcolors.ENDC,str(req['tags']).replace("u'",'').replace("'",""),\
                        ', '+bcolors.CYAN+'Generators='+ bcolors.ENDC,req['name_of_fragment'],\
                        ', '+bcolors.CYAN+'Name of Fragment='+ bcolors.ENDC,req['name_of_fragment'],\
                        ', '+bcolors.CYAN+'Notes='+ bcolors.ENDC,req['notes'],\
                        ''+ bcolors.ENDC
              if listAttr > 2 and listAttr < 6:
                  print bcolors.BLUE +\
                        'Creator Name='+ bcolors.ENDC,req['history'][0]['updater']['author_name'],\
                        '(',req['history'][0]['updater']['author_email'],')',\
                        'on',req['history'][0]['updater']['submission_date'],\
                        '\n'\
                        + bcolors.Gray_like_Ghost +\
                        'McM View Link= https://cms-pdmv.cern.ch/mcm/requests?shown=2199023255551&prepid='+req['prepid'],\
                        '\n'\
                        'McM Edit Link= https://cms-pdmv.cern.ch/mcm/edit?db_name=requests&prepid='+req['prepid'],\
                        ''+ bcolors.ENDC
              if listAttr > 3 and listAttr < 8:
                  print bcolors.YELLOW +\
                    'Member of chain(s)'
                  for current_chain in req['member_of_chain']:
                      query_chains = "member_of_chain="+current_chain
                      # print "req['member_of_chain'][0]",query_chains
                      temp = sys.stdout
                      f = open('/dev/null', 'w')
                      sys.stdout = f
                      chained_prepIds=getMcMlist(query_chains,False)
                      sys.stdout = temp
                      prepid1 = []
                      for req1 in chained_prepIds:
                        prepid1.append(req1['prepid'])
                        prepid1.append('Approv/Status: '+str(req1['approval'])+'/'+str(req1['status']))
                        prepid1.append('Compl Evts: '+str(req1['completed_events'])+'/'+str(req1['total_events']))
                        prepid1.append('Prio: '+str(req1['priority']))
                        prepid1.append('Last update:  '+str(req1['history'][len(req1['history'])-1]['action'])+' '+str(req1['history'][len(req1['history'])-1]['updater']['submission_date']))
                        if 'GS' not in req1['prepid'] and 'Mini' not in req1['prepid'] and len(req1['reqmgr_name']) > 0:
                          gif = str(req1['reqmgr_name'][0]['name'].replace('pdmvserv_task_','').replace(req1['prepid'],'').replace('__','/').replace('_','/'))+'.gif'
                          prepid1.append('Events growth Link:  https://cms-pdmv.web.cern.ch/cms-pdmv/stats/growth/pdmvserv/task/'+str(req1['prepid'])+gif)
                        else: prepid1.append('')
                        n=6
                      prepid1 = [prepid1[i:i+n] for i in range(0, len(prepid1), n)]
                      print current_chain+" : "+ bcolors.ENDC
                      for prepid in prepid1[::-1]:
                        print str(prepid).strip('[').strip(']').replace("u'",'').replace("'","").replace(",","\t||\t")
                      if listAttr < 6: print bcolors.Gray_like_Ghost +\
                      'McM View Link= https://cms-pdmv.cern.ch/mcm/chained_requests?shown=4095&prepid='+current_chain,\
                      ''+ bcolors.YELLOW
                      else: print '\n'
              elif listAttr == 8:
                  # print bcolors.YELLOW +\
                    # 'Member of chain(s)'
                  prepid1 = []
                  for current_chain in req['member_of_chain']:
                      query_chains = "member_of_chain="+current_chain
                      temp = sys.stdout
                      f = open('/dev/null', 'w')
                      sys.stdout = f
                      chained_prepIds=getMcMlist(query_chains,False)
                      sys.stdout = temp
                      if not chained_prepIds: continue
                      for req1 in chained_prepIds:
                        if not ('MiniAOD' in str(req1['prepid']) or 'DR76' in str(req1['prepid']) or 'reHLT' in str(req1['prepid'])):
                            prepid1.append( str(req1['prepid'])+' '+str(req1['completed_events']) )
                  counter = 0
                  # prepid1 = [prepid for prepid in prepid1 if ('GS' in prepid or 'LHE' in prepid)]
                  for prepid in set(prepid1):
                      arrow = ''
                      if counter < len(set(prepid1))-1:
                          arrow = ' -> '
                      counter = counter+1
                      print str(prepid).strip('[').strip(']').replace("u'",'').replace("'","").replace(","," ")+arrow,
                  print ''
              if listAttr > 4 and listAttr < 6:
                  print bcolors.WHITE +'Fragment code=\n'+\
                        bcolors.Gray_like_Ghost +\
                        req['fragment'],\
                        ''+ bcolors.ENDC
              print bcolors.ENDC
        
              if listAttr > 1 and listAttr < 8: print '======================================================================================================================================================================\n\n',\
        
def getPrepIDList(query_string, getNew, getForValidation, getChain):
    req_list = getMcMlist(query_string,True)

    event_sum = 0
    out_list = []
    if req_list is None:
        print "\033[1;31mCould not get requests from McM\033[1;m"
    else:
        for req in req_list:
            if getNew:
                if req['time_event'] != -1 or req['size_event'] != -1:
                    continue
            if getForValidation:
                if req['time_event'] <= 0 or req['size_event'] <= 0:
                    continue
            if not getChain:
                out_list.append(req['prepid'])
                event_sum += req['total_events']
            else:
                out_list.append(req['member_of_chain'][0])
    print "Found {0} requests with {1}M events".format(len(out_list),
                                                       event_sum/1e6)
    return out_list


def isSequential(lastID, currentID):
    last = lastID.split('-')
    current = currentID.split('-')

    if len(last) == 3 and len(current) == 3:
        if last[0] == current[0] and last[1] == current[1] \
                and int(last[2]) + 1 == int(current[2]):
            return True
    return False


def printList(list, format):
    arrow = "-"
    comma = ","
    if format == 1:
        arrow = " ---> "
        comma = ", "
    elif format == 2:
        arrow = " ---> "
        comma = "<br>"

    lastID = "FIRST"
    print_last = False
    last_index = len(list) - 1
    print ""
    for i, PrepID in enumerate(list):
        if isSequential(lastID, PrepID):
            if i < last_index:
                print_last = True
            else:
                sys.stdout.write("{0}{1}".format(arrow, PrepID))
        else:
            if print_last:
                sys.stdout.write("{0}{1}{2}{3}".format(arrow, lastID, comma,
                                                     PrepID))
            elif i > 0:
                sys.stdout.write("{0}{1}".format(comma, PrepID))
            else:
                sys.stdout.write("{0}".format(PrepID))
            print_last = False
        lastID = PrepID
    print "\n"
    return


def main():
    args = getArguments() # Setup flags and get arguments

    if args.listAttr < 0:
        list = getPrepIDList(args.query, args.getNew, args.getForValidation,
                             args.getChain)
        printList(list, args.format)
    else:
        dict = getPrepIDListWithAttributes(args.query,args.listAttr)
        
    return


if __name__ == '__main__':
    main()
