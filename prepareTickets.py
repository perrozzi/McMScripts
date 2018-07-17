import collections
from collections import defaultdict
import sys
import os.path
import argparse
import csv
import pprint
import time
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM

useDev = False
mcm = McM( dev=useDev ) # Get McM connection
# pwgs=mcm.get('/restapi/users/get_pwg')['results']
pwgs = ['HIG']
print 'pwgs',pwgs
#Pair between
ochain = 'chain_RunIIWinter15pLHE_flowRunIISpring15FSPreMix_flowRunIISpring15MiniAODv2'
dchain = 'RunIISpring15FSPreMixMiniAODv2PLHE'
createTicket = False
# createTicket = True
collector=defaultdict(lambda : defaultdict( lambda : defaultdict( int )))
print 50*"-"
for pwg in pwgs:
    print "\t",pwg
    ## get all chains from that pwg in that chained campaign
    crs = mcm.get('chained_requests', query='member_of_campaign=%s&pwg=%s'%(ochain,pwg))
    for cr in crs:
      root_id = cr['chain'][0]
      print "\t\t",root_id
      campaign = root_id.split('-')[1]
      collector[pwg][campaign][root_id]+=1
print "This is the list of %s requests that are deemed chainable for miniaod round 2"%(pwgs)
print 'collector',collector
all_ticket=[]
for pwg in pwgs:
    ## create a ticket for the correct chain
    ccs = mcm.get('chained_campaigns', query='alias=%s'%(dchain))
    for cc in ccs:
        alias = cc['alias']
        root_campaign = cc['campaigns'][0][0]
        for repeat in range(10):
            requests_for_that_repeat = map(lambda i : i[0], filter(lambda i : i[1]==repeat, collector[pwg][root_campaign].items()))
            if not requests_for_that_repeat: continue
            print requests_for_that_repeat
            requests_for_that_repeat.sort()
            ## create a ticket with that content
            mccm_ticket = { 'prepid' : pwg, ## this is how one passes it in the first place
                            'pwg' : pwg,
                            'requests' : requests_for_that_repeat,
                            'notes' : "Second round of miniaod in RunIIFall15MiniAODv2",
                            'chains' : [ alias ],
                            'repetitions' : repeat,
                            'block' : 3
                          }
            print mccm_ticket
            all_ticket.append( copy.deepcopy( mccm_ticket ) )
## you'll be able to re-read all tickets from the created json
open('all_tickets.json','w').write(json.dumps( all_ticket))

all_ticket = json.loads(open('all_tickets.json').read())
for ticket in all_ticket:
    ### flip the switch (set it to false first, see if all requests you need are in the ticket)
    if createTicket:
        mcm.put('mccms', ticket )
        time.sleep(5)
    pass

