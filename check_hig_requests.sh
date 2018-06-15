#!/bin/bash

cd /afs/cern.ch/work/p/perrozzi/private/git/Hbb/validations/CMSSW_7_1_31/src; eval `scramv1 runtime -sh`; cd -
cern-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm/ -o ~/private/prod-cookie.txt --krb --reprocess
cern-get-sso-cookie -u https://cms-pdmv-dev.cern.ch/mcm/ -o ~/private/dev-cookie.txt --krb --reprocess

pwgs=( 'HIG' 'SUS' 'SMP' 'TOP' 'EXO' 'BPH' 'BTV' 'B2G' 'JME' 'MUO' 'FSQ' )
prepids=( 'RunIIFall17*GS*' 'Summer18*GS*' )
statuses=( 'new' 'validation' 'defined' 'approved' 'submitted' )
# pwgs=( 'HIG' )
# prepids=( 'RunIIFall17wmLHEGS-019')
# statuses=( 'new' 'validation' 'defined' 'approved' 'submitted' 'done' )

for pwg in "${pwgs[@]}"; do
  for prepid in "${prepids[@]}"; do
    for status in "${statuses[@]}"; do
        python /afs/cern.ch/work/p/perrozzi/private/git/Hbb/McMScripts/check_hig_requests.py $pwg $prepid $status
        # echo "check_hig_requests_single.sh" $pwg $prepid $status
        # bsub -u pippo123 -q 8nh check_hig_requests_single.sh $pwg $prepid $status
    done
  done
done

# sendmail cms-higgs-mc_contacts@cern.ch < automatic_mail.txt
# sendmail perrozzi@cern.ch < automatic_mail.txt
