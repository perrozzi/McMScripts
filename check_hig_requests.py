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
move_files_to_www = True
# move_files_to_www = False

pwgs=['HIG','SUS','SMP','TOP','EXO','BPH','BTV','B2G','JME','MUO','FSQ']
tags=['*']
prepids=['RunIIFall17*GS*']
order=['1','2','3','4','5','6']
statuses=['new','validation','defined','approved','submitted','done']
actors=[]

# pwgs=['BTV']
# tags=['*']
# prepids=['RunIIFall17*GS*']
# order=['2','5']
# statuses=['validation','submitted']
# actors=[]


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
    file.write('<table id="myTable2" style="font-size:85%" border="1" CELLPADDING="4">\n')
    counter = 0
    for element in data:
        if counter % row_length == 0:
            file.write('<tr>\n')
        file.write('<td><b>%s</b></td>' % element)
        counter += 1
        if counter % row_length == 0:
            file.write('</tr>\n')
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            file.write('<td>&nbsp;</td>\n')
        file.write('</tr>\n')

def print_div_header(data, row_length,file):
    file.write('<div id="grid" style="font-size:80%" border="1">\n')
    counter = 0
    for element in data:
        file.write('<div><b>%s</b></div>' % element)
        counter += 1
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            file.write('<div>&nbsp;</div>\n')

def print_table_footer(file):
    file.write('</table>\n')

def print_div_footer(file):
    file.write('</div>\n')

def print_table(data, row_length):
    counter = 0
    for element in data:
        if counter % row_length == 0:
            file.write('<tr>\n')
        file.write('<td id="td2">%s</td>' % element)
        counter += 1
        if counter % row_length == 0:
            file.write('</tr>\n')
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            file.write('<td id="td2">&nbsp;</td>\n')
        file.write('</tr>\n')

def print_div(data, row_length,file):
    counter = 0
    for element in data:
        file.write('<div>%s</div>' % element)
        counter += 1
    if counter % row_length != 0:
        for i in range(0, row_length - counter % row_length):
            file.write('<div>&nbsp;</div>\n')

def getMcMlist(query_string,printout):
    useDev = False
    mcm = restful( dev=useDev ) # Get McM connection
    req_list = mcm.getA('requests', query=query_string)
    return req_list

def getPrepIDListWithAttributes(query_string,tag,file):
    file.write('<head>\n')
    file.write('<script src="../sorttable.js"></script>\n')
    file.write('<script>\n')
    file.write('function myFunction() {\n')
    file.write('  // Declare variables \n')
    file.write('  var input, filter, table, tr, td, i;\n')
    file.write('  input = document.getElementById("myInput");\n')
    file.write('  filter = input.value.toUpperCase();\n')
    file.write('  table = document.getElementById("myTable");\n')
    file.write('  tr = table.getElementsByTagName("tr");\n')
    file.write('  // Loop through all table rows, and hide those who don\'t match the search query\n')
    file.write('  for (i = 0; i < tr.length; i++) {\n')
    file.write('    td = tr[i].getElementsByTagName("td")[0];\n')
    file.write('    if (td) {\n')
    file.write('      id = td.id;\n')
    # file.write('      if (id = "td1"){\n')
    # file.write('      if (td.innerHTML = "bookmark"){\n')
    # file.write('       document.write(id);\n')
    # file.write('       document.write(td.innerHTML);\n')
    file.write('       if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {\n')
    file.write('          tr[i].style.display = "";\n')
    file.write('       } else {\n')
    file.write('          tr[i].style.display = "none";\n')
    file.write('       }\n')
    # file.write('      }\n')
    file.write('    } \n')
    file.write('  }\n')
    file.write('}\n')
    file.write('function myFunction2() {\n')
    file.write('  // Declare variables \n')
    file.write('  var input, filter, table, tr, td, i;\n')
    file.write('  input = document.getElementById("myInput2");\n')
    file.write('  filter = input.value.toUpperCase();\n')
    file.write('  table = document.getElementById("myTable");\n')
    file.write('  tr = table.getElementsByTagName("tr");\n')
    file.write('  // Loop through all table rows, and hide those who don\'t match the search query\n')
    file.write('  for (i = 0; i < tr.length; i++) {\n')
    file.write('    td = tr[i].getElementsByTagName("td")[1];\n')
    file.write('    if (td) {\n')
    file.write('      if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {\n')
    file.write('        tr[i].style.display = "";\n')
    file.write('      } else {\n')
    file.write('        tr[i].style.display = "none";\n')
    file.write('      }\n')
    file.write('    } \n')
    file.write('  }\n')
    file.write('}\n')
    file.write('</script> \n')
    
    file.write('</head>\n')
    file.write('<style>\n')
    file.write('#grid {\n')
    file.write('    display: grid;\n')
    file.write('    border:1px solid black;\n')
    file.write('    grid-template-columns: 25% 15% 25% 8% 7% 20%;\n')
    file.write('}\n')
    file.write('</style>\n')

    file.write('<font size="5">MCM query string: <b> <a href="https://cms-pdmv.cern.ch/mcm/requests?' + query_string + '" target="_blank">'+query_string+'</a></b> </font>\n')
    file.write('<br> <br> Last update on: <b>' + str(datetime.datetime.now()) + '</b>\n')
    temp = sys.stdout
    f = open('/dev/null', 'w')
    sys.stdout = f
    req_list = getMcMlist(query_string,True)
    sys.stdout = temp
    
    file.write('<br>\n')
    file.write('<input type="text" id="myInput" onkeyup="myFunction()" placeholder="Search for dataset names..">\n')
    file.write('<input type="text" id="myInput2" onkeyup="myFunction2()" placeholder="Search for prepids..">\n')
    file.write('<table id="myTable" class="sortable" border="1" CELLPADDING="4">\n')
    file.write('<tr class="header">\n')
    file.write('<th >Dataset name</th>\n')
    file.write('<th >prepid</th>\n')
    file.write('<th >Extension</th>\n')
    file.write('<th >Chains</th>\n')
    file.write('</tr>\n')


    if req_list is None:
      file.write("Could not get requests from McM"); #return
    else: file.write('\n')
    for req in req_list:
        file.write('<tr>\n')
        file.write('<td id="td1">\n')
        file.write('<b>'+req['dataset_name']+'</b>\n')
        file.write('<br><br><a href="#'+req['prepid']+'">bookmark<a>\n')
        file.write('<td>\n')
        file.write(req['prepid'])
        file.write('<td>\n')
        file.write(str(req['extension']))

        file.write('<td>\n')
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
            file.write('<br><a href="https://cms-pdmv.cern.ch/mcm/chained_requests?shown=4095&prepid='+current_chain+'" target="_blank">'+current_chain+'</a>'+" : <br>")
            print_div_header(['prepid','Approv/Status','Compl Evts','Monitoring','Priority','Last update'],n,file)
            if prepid1 is not None:
              for prepid in prepid1[::-1]:
                prepid = [x for x in prepid if x is not None] 
                print_div(prepid,n,file)
            print_div_footer(file)
        
        file.write('<td>\n')
        file.write('</td>\n')
        file.write('</tr>\n')

    file.write('</table>\n')
    file.write('<br>Correctly finished listing requests<br>\n')

def main():
    
    file_extension = 'html'
    
    for pwg in pwgs:
      for tag in tags:
        for prepid in prepids:
          counter = 0
          for status in statuses:
            print 'processing',pwg+'_'+tag+'_'+prepid+'_'+order[counter]+'_'+status
            
            f = open(pwg+'_'+tag+'_'+prepid+'_'+order[counter]+'_'+status+'.'+file_extension, 'w')
            counter = counter+1
            
            dict = getPrepIDListWithAttributes('prepid=*'+pwg+'*'+prepid+'*&tags=*'+tag+'*&status='+status,tag,f)
            
            if move_files_to_www:
              os.system("mv "+pwg+"*"+prepid+"_*."+file_extension+" "+plot_dir)
    
    # if move_files_to_www:
      # os.system("wget https://dmytro.web.cern.ch/dmytro/cmsprodmon/images/campaign-RunningCpus.png; mv campaign-RunningCpus.png "+plot_dir)
      # os.system("wget https://dmytro.web.cern.ch/dmytro/cmsprodmon/images/prioritysummarycpusinuse.png; mv prioritysummarycpusinuse.png "+plot_dir)
      # os.system("wget https://dmytro.web.cern.ch/dmytro/cmsprodmon/images/prioritysummarycpuspending.png; mv prioritysummarycpuspending.png "+plot_dir)
    
    return

if __name__ == '__main__':
    main()
