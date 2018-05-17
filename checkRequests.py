#!/usr/bin/env python

################################
#
# checkRequests.py
#
#  Script to check the status of requests
#
#  author: David G. Sheffield (Rutgers)
#
################################

import sys
import os
import subprocess
import argparse
import csv
import pprint
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import * # Load class to access McM


def getArguments():
    parser = argparse.ArgumentParser(description='Test McM requests.')

    # Command line flags
    parser.add_argument('ids', help=
                        'List of PrepIDs to be checked. Separate range by -.')

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
        requests.append("{0}-{1}-{2:05d}".format(pwg, campaign, number))
    return requests


def parseIDList(compactList):
    splitList = compactList.split(',')
    requests = []
    for subList in splitList:
        splitSubList = subList.split('-')
        if len(splitSubList) == 3:
            requests.append(subList)
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
            sys.exit(3)
    return requests


def checkRequests(requests, useDev):
    mcm = restful(dev=useDev) # Get McM connection

    for PrepID in requests:
        failed_to_get = True
        for tries in range(3):
            base_req = mcm.getA('requests', PrepID)
            if base_req is not None:
                failed_to_get = False
                break
        if failed_to_get:
            print "\033[1;31mCould not get base request {0}\033[1;m\n".format(
                PrepID)
            continue
        print "{0} {1} ({2}/{3} or {4:3.1f}%)".format(PrepID, base_req['status'], base_req['completed_events'], base_req['total_events'], float(base_req['completed_events'])/float(base_req['total_events'])*100)

        for chainID in base_req['member_of_chain']:
            #print chainID
            failed_to_get = True
            for tries in range(3):
                chain_req = mcm.getA('chained_requests', chainID)
                if chain_req is not None:
                    failed_to_get = False
                    break
            if failed_to_get:
                print "\033[1;31mCould not get chain {0}\033[1;m\n".format(
                    chainID)
                continue
            space = ""
            for i, member in enumerate(chain_req['chain']):
                if i == 0:
                    continue
                space = space + " "
                failed_to_get = True
                for tries in range(3):
                    req = mcm.getA('requests', member)
                    if req is not None:
                        failed_to_get = False
                        break
                if failed_to_get:
                    print "\033[1;31mCould not get chained request {0}\033[1;m\n"\
                        .format(member)
                    continue
                print "{0}{1} {2} ({3}/{4} or {5:3.1f}%)".format(space, member, req['status'], req['completed_events'], req['total_events'], float(req['completed_events'])/float(req['total_events'])*100)
        print ""
    return


def main():
    args = getArguments() # Setup flags and get arguments

    requests = parseIDList(args.ids)
    useDev = False
    checkRequests(requests, useDev)

    return


if __name__ == '__main__':
    main()
