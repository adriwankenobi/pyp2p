#!/usr/bin/env python3
'''
Launches multiples p2p clients in ring format.
Works only on Mac.
'''

import argparse
import sys
import subprocess
import os


def readOptions(args=sys.argv[1:]):
    """ Reads options from command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", help="How many clients. Min 3.", type=int, required=True)
    parser.add_argument("-ip", "--ip", help="Base ip.", default="192.168.1.102")
    parser.add_argument("-p", "--port", help="Base port.", type=int, default=5000)
    parser.add_argument("-v", "--verbose", help="Debug mode.", default=False, action='store_true')
    opts = parser.parse_args(args)
    if opts.n < 3:
        print("Please enter min 3 clients")
        exit()
    return opts


def main():
    # Read options from command line
    opts = readOptions(sys.argv[1:])

    # Open n p2p clients in different terminals in ring format
    for i in range(0, opts.n):
        peerid = f'p{i}'
        port = opts.port + i
        predecesor = (i - 1) % opts.n
        p_port = opts.port + predecesor
        sucesor = (i + 1) % opts.n
        s_port = opts.port + sucesor
        knownpeers = f'p{predecesor}:{opts.ip}:{p_port},p{sucesor}:{opts.ip}:{s_port}'

        command = f'{os.getcwd()}/p2pclient.py -i {peerid} -p {port} -m 1024 -l {knownpeers}'
        if opts.verbose:
            command = f'{command} -v'

        subprocess.check_call(['osascript', '-e',
            f'tell application \"Terminal\" to do script \"{command}\"'])


if __name__ == '__main__':
    main()
