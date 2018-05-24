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
# print_to_screen = True

pwgs=['HIG','SUS','SMP','TOP','EXO','BPH','BTV','B2G','JME','MUO','FSQ']
tags=['*']
prepids=['RunIIFall17*GS*']
order=['1','2','3','4','5','6']
statuses=['new','validation','defined','approved','submitted','done']
actors=[]

# pwgs=['BTV']
# tags=['*']
# prepids=['RunIIFall17*GS*']
# order=['5']
# statuses=['submitted']
# actors=[]


screen_output = sys.stdout
file_output = sys.stdout

class bcolors:
    MAGENTA = '\033[35m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
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
    # print '<table class="sortable" style="font-size:85%" border="1" CELLPADDING="4">'
    print '<table id="myTable2" style="font-size:85%" border="1" CELLPADDING="4">'
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

def print_div_header(data, row_length):
    # print '<table class="sortable" style="font-size:85%" border="1" CELLPADDING="4">'
    # print '<table id="myTable2" style="font-size:85%" border="1" CELLPADDING="4">'
    print '<div id="grid" style="font-size:80%" border="1">'
    counter = 0
    for element in data:
        # if counter % row_length == 0:
            # print '<br>'
        print '<div><b>%s</b></div>' % element
        counter += 1
        # if counter % row_length == 0:
            # print '</tr>'
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            print '<div>&nbsp;</div>'
        # print '</tr>'

def print_table_footer():
    print '</table>'

def print_div_footer():
    print '</div>'

def print_table(data, row_length):
    counter = 0
    for element in data:
        if counter % row_length == 0:
            print '<tr>'
        print '<td id="td2">%s</td>' % element
        counter += 1
        if counter % row_length == 0:
            print '</tr>'
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            print '<td id="td2">&nbsp;</td>'
        print '</tr>'

def print_div(data, row_length):
    counter = 0
    for element in data:
        # if counter % row_length == 0:
            # print '<br>'
        print '<div>%s</div>' % element
        counter += 1
        # if counter % row_length == 0:
            # print '</tr>'
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            print '<div>&nbsp;</div>'
        # print '</tr>'

def getMcMlist(query_string,printout):
    useDev = False
    mcm = restful( dev=useDev ) # Get McM connection
    req_list = mcm.getA('requests', query=query_string)
    return req_list

def getPrepIDListWithAttributes(query_string,tag):
    print '<head>'
    print '<script src="../sorttable.js"></script>'
    print '<script>'
    print 'function myFunction() {'
    print '  // Declare variables '
    print '  var input, filter, table, tr, td, i;'
    print '  input = document.getElementById("myInput");'
    print '  filter = input.value.toUpperCase();'
    print '  table = document.getElementById("myTable");'
    print '  tr = table.getElementsByTagName("tr");'
    print '  // Loop through all table rows, and hide those who don\'t match the search query'
    # print '  Elements columns = document.select("body > table > td:not(:has(table))");'
    print '  for (i = 0; i < tr.length; i++) {'
    print '    td = tr[i].getElementsByTagName("td")[0];'
    print '    if (td) {'
    print '      id = td.id;'
    # print '      if (id = "td1"){'
    # print '      if (td.innerHTML = "bookmark"){'
    # print '       document.write(id);'
    # print '       document.write(td.innerHTML);'
    print '       if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {'
    print '          tr[i].style.display = "";'
    print '       } else {'
    print '          tr[i].style.display = "none";'
    print '       }'
    # print '      }'
    print '    } '
    print '  }'
    print '}'
    print 'function myFunction2() {'
    print '  // Declare variables '
    print '  var input, filter, table, tr, td, i;'
    print '  input = document.getElementById("myInput2");'
    print '  filter = input.value.toUpperCase();'
    print '  table = document.getElementById("myTable");'
    print '  tr = table.getElementsByTagName("tr");'
    print '  // Loop through all table rows, and hide those who don\'t match the search query'
    print '  for (i = 0; i < tr.length; i++) {'
    print '    td = tr[i].getElementsByTagName("td")[1];'
    print '    if (td) {'
    print '      if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {'
    print '        tr[i].style.display = "";'
    print '      } else {'
    print '        tr[i].style.display = "none";'
    print '      }'
    print '    } '
    print '  }'
    print '}'
    print '</script> '
    
    print '</head>'
    print '<style>'
    print '#grid {'
    print '    display: grid;'
    print '    border:1px solid black;'
    print '    grid-template-columns: 25% 15% 25% 8% 7% 20%;'
    print '}'
    print '</style>'

    print '<font size="5">MCM query string: <b> <a href="https://cms-pdmv.cern.ch/mcm/requests?' + query_string + '" target="_blank">'+query_string+'</a></b> </font>'
    print '<br> <br> Last update on: <b>' + str(datetime.datetime.now()) + '</b>'
    temp = sys.stdout
    f = open('/dev/null', 'w')
    sys.stdout = f
    req_list = getMcMlist(query_string,True)
    sys.stdout = temp
    
    print '<br>'
    print '<input type="text" id="myInput" onkeyup="myFunction()" placeholder="Search for dataset names..">'
    print '<input type="text" id="myInput2" onkeyup="myFunction2()" placeholder="Search for prepids..">'
    print '<table id="myTable" class="sortable" border="1" CELLPADDING="4">'
    print '<tr class="header">'
    print '<th >Dataset name</th>'
    print '<th >prepid</th>'
    print '<th >Extension</th>'
    print '<th >Chains</th>'
    print '</tr>'


    if req_list is None:
      print "Could not get requests from McM"; return
    else: print '\n'
    for req in req_list:
        # print '<hr>'
        print '<tr>'
        print '<td id="td1">'
        print '<b>'+req['dataset_name']+'</b>'
        print '<br><br><a href="#'+req['prepid']+'">bookmark<a>'
        # print '</td>'
        print '<td>'
        print req['prepid']
        # print '</td>'
        print '<td>'
        print req['extension']
        # print '</td>'
        # print '<td>'
        # print '</td>'

        print '<td>'
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
                prepid1.append(str("{:,}".format(req1['completed_events']))+'/'+max(1,str("{:,}".format(req1['total_events'])))+' (<b>'+format(100.*float(req1['completed_events'])/max(1,float(req1['total_events'])),'.1f')+'%</b>)')
                # if 'GS' not in req1['prepid'] and 'Mini' not in req1['prepid'] and len(req1['reqmgr_name']) > 0:
                if 'GS' in req1['prepid']:
                  dima='https://dmytro.web.cern.ch/dmytro/cmsprodmon/workflows.php?prep_id=task_'+req1['prepid']
                  prepid1.append('<a href="'+dima+'" target="_blank">prodmon</a>')
                  if len(req1['reqmgr_name']) > 0:
                    url = 'https://cms-pdmv.cern.ch/pmp/historical?r='+req1['reqmgr_name'][0]['name']
                    prepid1[len(prepid1)-1] = prepid1[len(prepid1)-1]+' <br> <a href="'+url+'" target="_blank">pmp</a>'
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
            # print_table_header(['prepid','Approv/Status','Compl Evts','Events growth','Priority','Last update'],n)
            print_div_header(['prepid','Approv/Status','Compl Evts','Monitoring','Priority','Last update'],n)
            if prepid1 is not None:
              for prepid in prepid1[::-1]:
                prepid = [x for x in prepid if x is not None] 
                # print_table(prepid,n)
                print_div(prepid,n)
            # print_table_footer()
            print_div_footer()
        
        print '<td>'
        print '</td>'
        print '</tr>'

    print '</table>'
    print '<br>Correctly finished listing requests<br>'

def main():
    
    screen_output = sys.stdout
    file_extension = 'html'
    
    for pwg in pwgs:
      for tag in tags:
        for prepid in prepids:
          counter = 0
          for status in statuses:
            sys.stdout = screen_output
            print 'processing',pwg+'_'+tag+'_'+prepid+'_'+order[counter]+'_'+status
            
            if not print_to_screen:
              f = open(pwg+'_'+tag+'_'+prepid+'_'+order[counter]+'_'+status+'.'+file_extension, 'w')
              file_output = f
              sys.stdout = file_output
            
            counter = counter+1
            
            dict = getPrepIDListWithAttributes('prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status,tag)
            
            if not print_to_screen:
              os.system("mv "+pwg+"*"+prepid+"_*."+file_extension+" "+plot_dir)
    
    return

if __name__ == '__main__':
    main()
