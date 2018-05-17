#!/usr/bin/env python

################################
#
#  check_hig_requests.py
#
#  Script to monitor requests and chains from McM
#
#  author: Luca Perrozzi, based on original scripts by David G. Sheffield
#
################################

import sys, os, re
import ntpath
import sys
import os.path
import argparse
import csv
import pprint
import time, datetime
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM
from requestClass import * # Load class to store request information

# plot_dir='/afs/cern.ch/user/p/perrozzi/www/work/MC_Higgs_testhmtl'
plot_dir='/afs/cern.ch/user/p/perrozzi/www/work/MC_Higgs'
print_to_screen = False
# print_to_screen = True
# pwgs=['HIG','SUS','SMP']
# pwgs=['HIG']
pwgs=['SUS','SMP','TOP','EXO','BPH','BTV','B2G''JME']
# tags=['HBB','HWW','HGG','HZZ','HTT','ttH','HH']
tags=['*']
# prepids=['LHE','GS','DR','Mini']
prepids=['RunIIFall17*GS*']
statuses=['new','validation','defined','approved','submitted','done'] #]
# actors=['perrozzi','obondu']
actors=[]

# actors=[]
# tags=['HBB']
# prepids=['DR']
# statuses=['submitted'] #]

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

def print_table_header(data, row_length):
    print '<table border="1" CELLPADDING="4">'
    counter = 0
    for element in data:
        if counter % row_length == 0:
            print '<tr>'
        print '<td><b>%s</b></td>' % element
        counter += 1
        if counter % row_length == 0:
            print '</tr>'
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            print '<td>&nbsp;</td>'
        print '</tr>'

def print_table_footer():
    print '</table>'

def print_table(data, row_length):
    # print '<table border="1">'
    counter = 0
    for element in data:
        if counter % row_length == 0:
            print '<tr>'
        print '<td>%s</td>' % element
        counter += 1
        if counter % row_length == 0:
            print '</tr>'
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            print '<td>&nbsp;</td>'
        print '</tr>'
    # print '</table>'

def getMcMlist(query_string,printout):
    useDev = False
    mcm = restful( dev=useDev ) # Get McM connection
    req_list = mcm.getA('requests', query=query_string)
    return req_list

def getPrepIDListWithAttributes(query_string,tag):
    print '<font size="5">MCM query string: <b> <a href="https://cms-pdmv.cern.ch/mcm/requests?' + query_string + '" target="_blank">'+query_string+'</a></b> </font>'
    print '<br> <br> Last update on: <b>' + str(datetime.datetime.now()) + '</b>'
    # return
    temp = sys.stdout
    f = open('/dev/null', 'w')
    sys.stdout = f
    req_list = getMcMlist(query_string,True)
    sys.stdout = temp
    
    if req_list is None:
      print "Could not get requests from McM"; return
    else: print '\n'
    for req in req_list:
        print '<hr>'
        # print 'prepid=',req['prepid'],', ',
        print '<br>Dataset name=<b>',req['dataset_name'],\
              '</b>, Extension=',req['extension'],
        # print', Completed/Total events=',str(req['completed_events'])+'/'+str(req['total_events']),\
              # '',
        # else: 
        # print '\t('+req['prepid']+')',
        print '<a name="'+req['prepid']+'"></a>('+req['prepid']+')',
        print '<a href="#'+req['prepid']+'">bookmark<a>','\n'
        # print '\n'

        # print '<br>Member of chain(s)<br>'
        print '<br>'
        chains = [x for x in req['member_of_chain'] if x is not None] 
        for current_chain in chains:           
            query_chains = "member_of_chain="+current_chain
            # print "req['member_of_chain'][0]",query_chains
            temp = sys.stdout
            f = open('/dev/null', 'w')
            sys.stdout = f
            chained_prepIds=getMcMlist(query_chains,False)
            sys.stdout = temp
            prepid1 = []
            if chained_prepIds is not None:
              for req1 in chained_prepIds:
                prepid1.append('<b>'+req1['prepid']+'</b>')
                prepid1.append(str(req1['approval'])+'/'+str(req1['status']))
                prepid1.append(str(req1['completed_events'])+'/'+max(1,str(req1['total_events']))+' (<b>'+format(100.*float(req1['completed_events'])/max(1,float(req1['total_events'])),'.1f')+'%</b>)')
                if 'GS' not in req1['prepid'] and 'Mini' not in req1['prepid'] and len(req1['reqmgr_name']) > 0:
                  # gif = str(req1['reqmgr_name'][0]['name'].replace('pdmvserv_task_','').replace(req1['prepid'],'').replace('__','/').replace('_','/'))+'.gif'
                  # url = 'https://cms-pdmv.web.cern.ch/cms-pdmv/stats/growth/pdmvserv/task/'+str(req1['prepid'])+gif
                  # gif = url.replace('\\n','').replace("'",'').replace(",",'')
                  # prepid_name = gif.split('/')[8]
                  # gif_name = str(req1['reqmgr_name'][0]['name'].replace('pdmvserv_task_','').replace(req1['prepid'],'').replace('__','_'))
                  # # print 'gif_name',gif_name
                  # # print('wget '+gif+'; mv '+ntpath.basename(gif)+' '+plot_dir+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+'.gif')
                  # os.system('wget '+gif+'; mv '+ntpath.basename(gif)+' '+plot_dir+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif')
                  # # prepid1.append('<a href="'+plot_dir.replace('/afs/cern.ch/user/p/perrozzi/www','https://perrozzi.web.cern.ch/perrozzi')+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif'+'" target="_blank">Link</a>')
                  # prepid1.append('<a href="'+plot_dir.replace('/afs/cern.ch/user/p/perrozzi/www','https://perrozzi.web.cern.ch/perrozzi')+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif'+'" target="_blank"><img src="'+plot_dir.replace('/afs/cern.ch/user/p/perrozzi/www','https://perrozzi.web.cern.ch/perrozzi')+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif" style="border: none; height: 100px;" ></a>')
                  # # prepid1.append('<a href="'+gif+'" target="_blank"><img src="'+gif+'" style="border: none; height: 100px;" ></a>')
                  prepid1.append('')
                else: 
                  prepid1.append('')
                prepid1.append(str(req1['priority']))
                date_modif = str(str(req1['history'][len(req1['history'])-1]['updater']['submission_date']))
                a = datetime.datetime.now().date()
                date_modif_list = date_modif.split('-')
                b = datetime.date(int(date_modif_list[0]),int(date_modif_list[1]),int(date_modif_list[2]))
                day_diff= (a-b).days
                prepid1.append(str(req1['history'][len(req1['history'])-1]['action'])+' '+str(req1['history'][len(req1['history'])-1]['updater']['submission_date'])+' (<b>'+str(day_diff)+' days ago</b>)')
            n=6
            prepid1 = [prepid1[i:i+n] for i in range(0, len(prepid1), n)]
            print '<br><a href="https://cms-pdmv.cern.ch/mcm/chained_requests?shown=4095&prepid='+current_chain+'" target="_blank">'+current_chain+'</a>'+" : <br>"
            print_table_header(['prepid','Approv/Status','Compl Evts','Events growth','Priority','Last update'],n)
            if prepid1 is not None:
              for prepid in prepid1[::-1]:
                # for item in prepid:
                  # item.replace(None,' ')
                  # item.replace('',' ')
                prepid = [x for x in prepid if x is not None] 
                # print str(prepid).strip('[').strip(']').replace("u'",'').replace("'","").replace(",","\t||\t")
                print_table(prepid,n)
                # print 'McM View Link= https://cms-pdmv.cern.ch/mcm/chained_requests?shown=4095&prepid='+current_chain
            print_table_footer()
        
        print '<br>'
    print '<br>Correctly finished listing requests<br>'
    # sys.exit()

def main():
    
    file_extension = 'html'
    # file_extension = 'log'
    
    for pwg in pwgs:
      for tag in tags:
        for prepid in prepids:
          counter = 1
          for status in statuses:
            # print pwg+'_'+tag+'_'+prepid+'_'+status
            
            if not print_to_screen:
              f = open(pwg+'_'+tag+'_'+prepid+'_'+str(counter)+'_'+status+'.'+file_extension, 'w')
              sys.stdout = f
            
            counter = counter+1
            
            dict = getPrepIDListWithAttributes('prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status,tag)
            # os.system('python getRequests.py -listattr 7 "prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status+'" 2>&1 >'+append+' log_'+pwg+'_'+tag+'_'+prepid+'_'+status+'.log')
            # sys.exit()
            
            if not print_to_screen:
              os.system("mv "+pwg+"*"+prepid+"_*."+file_extension+" "+plot_dir)
    
    # for actor in actors:
      # # for tag in tags:
        # for prepid in prepids:
          # for status in statuses:
            # # print pwg+'_'+tag+'_'+prepid+'_'+status
            
            # if not print_to_screen:
              # f = open('log_'+actor+'_'+prepid+'_'+status+'.'+file_extension, 'w')
              # sys.stdout = f
            
            # dict = getPrepIDListWithAttributes('actor='+actor+'&prepid=*'+prepid+'*&status='+status,'')
            # # os.system('python getRequests.py -listattr 7 "prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status+'" 2>&1 >'+append+' log_'+pwg+'_'+tag+'_'+prepid+'_'+status+'.log')
            # # sys.exit()
            
            # if not print_to_screen:
              # os.system("mv log_"+actor+"*."+file_extension+" "+plot_dir)

    return


if __name__ == '__main__':
    main()


# directory = time.strftime('%Y-%m-%d')
# if not os.path.exists(directory):
    # os.makedirs('~/www/work/MC_Higgs/'+directory)
    