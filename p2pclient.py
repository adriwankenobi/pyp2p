#!/usr/bin/env python3
'''
Launches a small p2p app.
'''

import sys
import argparse
import threading
import time
import json
from messages import messages
from peer import Peer
from router import distancerouter


def readOptions(args=sys.argv[1:]):
    """ Reads options from command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", help="Peer id. Format is 'p65'.", required=True)
    parser.add_argument("-p", "--port", type=int, help="Server port.", required=True)
    parser.add_argument("-m", "--maxpeers", type=int, help="Max number of peers.", required=True)
    parser.add_argument("-l", "--listofpeers",
        help="List of comma separated peers. E.g: p01:192.168.1.102:5001,p02:192.168.1.102:5002",
        required=True)
    parser.add_argument("-t", "--ttl", type=int,
        help="How deep the finding algorithm goes.", default=5)
    parser.add_argument("-b", "--backlog", type=int,
        help="Backlog for server connection.", default=5)
    parser.add_argument("-to", "--timeout", type=int,
        help="Timeout for server connection.", default=2)
    parser.add_argument("-v", "--verbose", help="Debug mode.", default=False, action='store_true')
    opts = parser.parse_args(args)
    opts.peers = []
    for p in opts.listofpeers.split(','):
        opts.peers.append(p)
    return opts


def myPingHandler(conn, msgdata):
    """ Handles the message PING """
    conn.send('RESP', 'PONG')


def myEchoHandler(conn, msgdata):
    """ Handles the message ECHO """
    conn.send('RESP', msgdata)


def myFindHandler(conn, msgdata, peerid, finder):
    """ Handles the message FIND """
    data = json.loads(msgdata)
    target = data['peerid']
    discarded = set(data['discarded'])
    ttl = data['ttl']

    host, port, discarded = finder(target, ttl, discarded)
    response = {'peerid': target}
    if (host, port) != (None, None):
        response['host'] = host
        response['port'] = port
    else:
        discarded.add(peerid)
        response['discarded'] = list(discarded)

    conn.send('RESP', str(json.dumps(response)))


def myAsyncHandler(conn, msgdata, responder):
    """ Handles the message ASYN """
    # Simulates processing data
    time.sleep(3)
    data = json.loads(msgdata)
    # Echoes the data
    responder(data['sender'], 'ARES', data['data'], False)


def myAsyncResponseHandler(conn, msgdata):
    """ Handles the message ARES """
    print(f'[{conn.s.getpeername()}] -> {msgdata}')


# Messages definitions
messages = {
    'PING': messages['PING'].addHandler(myPingHandler),
    'ECHO': messages['ECHO'].addHandler(myEchoHandler),
    'FIND': messages['FIND'].addHandler(myFindHandler),
    'ASYN': messages['ASYN'].addHandler(myAsyncHandler),
    'ARES': messages['ARES'].addHandler(myAsyncResponseHandler)
}


def menu():
    """ Prints the menu options for the client """
    print('--------------------------------------')
    print('Send a message to a peer')
    print('usage: MSGTYPE PEER [MSGDATA]')
    print('E.g: ECHO p01 Hello World!')
    print('Available message types:')
    for m in messages:
        if messages[m].iscallable:
            print(f'- {m}: {messages[m].helper}')
    print('Exit: Ctrl+C')
    print('--------------------------------------')


def main():
    # Read options from command line
    opts = readOptions(sys.argv[1:])

    # Init peer
    mypeer = Peer(opts.id, opts.maxpeers, opts.port, opts.ttl, opts.verbose)

    # Add list of known peers
    for p in opts.peers:
        pfull = p.split(':')
        mypeer.addpeer(pfull[0], pfull[1], int(pfull[2]))

    # Add handlers
    for m in messages:
        mypeer.addhandler(m, messages[m].handler)

    # Add router
    mypeer.addrouter(distancerouter)

    # Start peer server in a separate thread
    t = threading.Thread( target = mypeer.start, args = [opts.backlog, opts.timeout] )
    t.daemon = True
    t.start()
    print(f'Peer {mypeer.host}:{mypeer.port} started')

    # Start client
    menu()
    try:
        for line in sys.stdin:
            line = line.rstrip().split(' ', 2)
            msgtype = line[0].upper()
            target = line[1]
            if msgtype not in messages or not messages[msgtype].iscallable:
                print('Wrong message type. Please try again.')
                continue
            data = ''
            if len(line) == 3:
                data = line[2]
            if messages[msgtype].isasync:
                # Need to add own info as sender for async messages, so receiver can respond
                data = json.dumps({'data': data, 'sender': mypeer.peerid})
            res = mypeer.sendtopeer(target, msgtype, data, not messages[msgtype].isasync)
            for r in res:
                if r[0] == 'ERRO':
                    print(f'{r[1]}')
                    break
                if r[0] == 'RESP':
                    print(f'[{target}] -> {r[1]}')
                    continue
                print('Unable to process response.')
                continue
            menu()

    except KeyboardInterrupt:
        exit()

if __name__ == '__main__':
    main()
