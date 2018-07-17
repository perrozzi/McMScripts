#!/usr/bin/env python

################################
#
# validateChains
#
#  Script to validate a range of chained
#  request PrepIDs at once.
#
#  author: David G. Sheffield (Rutgers)
#
################################

import sys
import os.path
import argparse
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM


def getArguments():
    parser = argparse.ArgumentParser(description='Validate chains in McM.')

    # Command line flags
    parser.add_argument('ids', metavar='PrepIDs',
                        help='List of PrepIDs for chains to be validated.')

    args_ = parser.parse_args()
    return args_


def fillIDRange(pwg, campaign, first, last):
    first = int(first)
    last = int(last)
    chains = []
    if first > last:
        print "Error: PrepID range out of order. {0}-{1}-{2:05d} > {0}-{1}-{3:05d}".format(
            pwg, campaign, first, last)
        sys.exit(1)

    for number in range(first, last+1):
        chains.append("{0}-{1}-{2:05d}".format(pwg, campaign, number))
    return chains


def parseIDList(compactList):
    print compactList
    splitList = compactList.split(',')
    chains = []
    for subList in splitList:
        splitSubList = subList.split('-')
        if len(splitSubList) == 3:
            chains.append(subList)
        elif len(splitSubList) == 4:
            chains += fillIDRange(splitSubList[0], splitSubList[1],
                                  splitSubList[2], splitSubList[3])
        elif len(splitSubList) == 6:
            if splitSubList[0] != splitSubList[3]:
                print "Error: PrepID range must be for the same PWG."
                sys.exit(1)
            if splitSubList[1] != splitSubList[4]:
                print "Error: PrepID range must be for the same chained campaign."
                sys.exit(1)
            chains += fillIDRange(splitSubList[0], splitSubList[1],
                                  splitSubList[2], splitSubList[5])
        else:
            print "Error: Poorly formed PrepID list."
            sys.exit(1)
    return chains


def validate(chains):
    mcm = McM(dev=False)

    print "Validating {0} chained requests".format(len(chains))
    for PrepID in chains:
        url = 'restapi/chained_requests/test/{0}'.format(PrepID)
        chain_output = mcm.get(url)

        if chain_output['results']:
            print "{0} validating".format(PrepID)
        else:
            print "{0} will not be validated, due to the following reason:\n{1}".format(
                PrepID, chain_output['message'])


def main():
    args = getArguments()          # Setup flags and get arguments
    chains = parseIDList(args.ids) # Get list of chains and check args
    validate(chains)               # Tell McM to validate chains


if __name__ == '__main__':
    main()
