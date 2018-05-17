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

plot_dir='/afs/cern.ch/user/p/perrozzi/www/work/MC_Higgs'
print_to_screen = False
# pwgs=['HIG']
# tags=['HBB','HWW','HGG','HZZ','HTT','ttH']
# prepids=['LHE','GS','DR','Mini']
# statuses=['new','validation','defined','approved','submitted']
pwgs=['HIG']
tags=['HBB']
prepids=['DR']
statuses=['submitted']

def print_table_header(data, row_length):
    print '<table border="1" CELLPADDING="5">'
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

def getMcMlist(query_string,printout):
    useDev = False
    mcm = restful( dev=useDev ) # Get McM connection
    req_list = mcm.getA('requests', query=query_string)
    return req_list

def getPrepIDListWithAttributes(query_string,tag):
    print '<font size="5">MCM query string: <b>' + query_string + '</b> </font>'
    print '<br> <br> Last update on: <b>' + str(datetime.datetime.now()) + '</b>'
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
        print '<br>Dataset name=<b>',req['dataset_name'],\
              '</b>, Extension=',req['extension'],
        print '\t(<a href="#'+req['prepid']+'">'+req['prepid']+'<a>)','\n'

        print '<br>'
        chains = [x for x in req['member_of_chain'] if x is not None] 
        for current_chain in chains:           
            query_chains = "member_of_chain="+current_chain
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
                prepid1.append(str(req1['completed_events'])+'/'+str(req1['total_events'])+' (<b>'+format(100.*float(req1['completed_events'])/float(req1['total_events']),'.1f')+'%</b>)')
                if 'GS' not in req1['prepid'] and 'Mini' not in req1['prepid'] and len(req1['reqmgr_name']) > 0:
                  gif = str(req1['reqmgr_name'][0]['name'].replace('pdmvserv_task_','').replace(req1['prepid'],'').replace('__','/').replace('_','/'))+'.gif'
                  url = 'https://cms-pdmv.web.cern.ch/cms-pdmv/stats/growth/pdmvserv/task/'+str(req1['prepid'])+gif
                  gif = url.replace('\\n','').replace("'",'').replace(",",'')
                  prepid_name = gif.split('/')[8]
                  gif_name = str(req1['reqmgr_name'][0]['name'].replace('pdmvserv_task_','').replace(req1['prepid'],'').replace('__','_'))
                  os.system('wget '+gif+'; mv '+ntpath.basename(gif)+' '+plot_dir+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif')
                  prepid1.append('<a href="'+plot_dir.replace('/afs/cern.ch/user/p/perrozzi/www','https://perrozzi.web.cern.ch/perrozzi')+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif'+'" target="_blank"><img src="'+plot_dir.replace('/afs/cern.ch/user/p/perrozzi/www','https://perrozzi.web.cern.ch/perrozzi')+'/plots/'+req1['dataset_name']+'_'+tag+'_'+prepid_name+gif_name+'.gif" style="border: none; height: 100px;" ></a>')
                else: prepid1.append('')
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
                prepid = [x for x in prepid if x is not None] 
                print_table(prepid,n)
            print_table_footer()
        
        print '<br>'

def main():
    
    file_extension = 'html'
    
    for pwg in pwgs:
      for tag in tags:
        for prepid in prepids:
          for status in statuses:
            
            if not print_to_screen:
              f = open('log_'+pwg+'_'+tag+'_'+prepid+'_'+status+'.'+file_extension, 'w')
              sys.stdout = f
            
            dict = getPrepIDListWithAttributes('prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status,tag)
            
            if not print_to_screen:
              os.system("mv log_HIG_*."+file_extension+" "+plot_dir)

    return


if __name__ == '__main__':
    main()
