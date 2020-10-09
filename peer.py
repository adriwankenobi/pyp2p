#!/usr/bin/python3
'''
Provides p2p functionality .
'''

import socket
import threading
import json
from messages import messages
from peerconnection import PeerConnection


class Peer:
    """ Implements the p2p functionality """


    def __init__(self, peerid, maxpeers, port, ttl, debug):
        """ Initializes a peer """

        self.peerid = peerid
        self.maxpeers = maxpeers
        self.port = port
        self.ttl = ttl
        self.debug = debug

        # Find local IP by connecting somewhere
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("www.google.com", 80))
        self.host = s.getsockname()[0]
        s.close()

        self.peers = {}
        self.shutdown = False

        self.handlers = {}
        self.router = None


    def __debug(self, message):
        """ Prints a message in debug mode """
        if self.debug:
            print(f'[DEBUG] {message}')


    def __handle(self, csock):
        """ Handles connected client """

        host, port = csock.getpeername()
        conn = PeerConnection(host, port, csock)

        try:
            msgtype, msgdata = conn.receive()
            self.__debug(f'[{host}:{port}] -> {msgtype}:{msgdata}')

            # Ignore unknown message types
            if msgtype in self.handlers:
                if msgtype == 'FIND':
                    self.handlers[msgtype](conn, msgdata, self.peerid, self.findpeer)
                elif messages[msgtype].isasync:
                    self.handlers[msgtype](conn, msgdata, self.sendtopeer)
                else:
                    self.handlers[msgtype](conn, msgdata)

        except KeyboardInterrupt:
            raise

        conn.close()


    def addhandler(self, msgtype, handler):
        """ Registers a handler """

        assert len(msgtype) == 4
        self.handlers[msgtype] = handler


    def addrouter(self, router):
        """ Registers the routing algorithm """
        self.router = router


    def addpeer(self, peerid, host, port):
        """ Adds a peer to the known list of peers """

        if peerid not in self.peers and len(self.peers) < self.maxpeers:
            self.peers[peerid] = (host, port)


    def findpeer(self, peerid, ttl, discarded=set()):
        """ Tries to find a peer """

        while True:

            if self.router:
                # Select which peer to check next
                nextpeerid, host, port = self.router(peerid, self.peers, self.maxpeers, discarded)

            if not self.router or not nextpeerid:
                # There is no more peers to check, failure
                return None, None, discarded

            if nextpeerid == peerid:
                # Target peer has been found
                res = self.__send(nextpeerid, host, port, 'PING')
                if res[0][0] == 'RESP' and res[0][1] == 'PONG':
                    # Peer is online, success
                    self.__debug(f'Peer {nextpeerid} is online!')
                    break
                # Peer is offline, discarding it, try more
                self.__debug(f'Peer {nextpeerid} is offline :(')
                discarded.add(nextpeerid)
                continue

            # We've gone too deep in the search tree, failure
            self.__debug(f'TTL: {ttl}')
            if ttl <= 0:
                return None, None, discarded

            # Discard self to avoid infinite loop
            discarded.add(self.peerid)
            data = json.dumps({"peerid": peerid, "discarded": list(discarded), "ttl": ttl - 1})

            # Go search on the selected next peer
            res = self.__send(nextpeerid, host, port, 'FIND', str(data))
            if res[0][0] != 'RESP':
                # No response, selected peer is offline, discard it
                discarded.add(nextpeerid)
                # Allow search in self again, we might still have unchecked known peers
                discarded.remove(self.peerid)
                continue

            # Selected peer is online
            data = json.loads(res[0][1])
            if 'host' not in data and 'port' not in data:
                # Selected peer didn't find the target, discard it
                discarded = set(data['discarded'])
                # Allow search in self again, we might still have unchecked known peers
                discarded.remove(self.peerid)
                continue

            # Selected peer found the target along the way
            host = data['host']
            port = data['port']
            break

        return host, port, discarded


    def sendtopeer(self, peerid, msgtype, msgdata, wait=True):
        """ Sends message to another peer """

        if peerid == self.peerid:
            host = self.host
            port = self.port
        else:
            host, port, _ = self.findpeer(peerid, self.ttl)
            if (host, port) == (None, None):
                return [('ERRO', f'Unable to find {peerid}')]

        return self.__send(peerid, host, port, msgtype, msgdata, wait)


    def __send(self, peerid, host, port, msgtype, msgdata='', wait=True):
        """ Sends message to another peer """

        self.__debug(f'{msgtype} -> {peerid}')
        response = []
        try:
            conn = PeerConnection(host, port)
            conn.send(msgtype, msgdata)

            if wait:
                r = conn.receive()
                while (r != (None, None)):
                    self.__debug(f'[{peerid}] -> {r[0]}:{r[1]}')
                    response.append(r)
                    r = conn.receive()
            conn.close()

        except KeyboardInterrupt:
            raise

        except ConnectionRefusedError:
            return [('ERRO', f'Peer {peerid} is offline')]

        return response


    def start(self, backlog=5, timeout=2):
        """ Starts the peer server """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(backlog)
        s.settimeout(timeout)

        while not self.shutdown:
            try:
                csock, _ = s.accept()
                csock.settimeout(None)

                # Start handler in a separate thread
                t = threading.Thread(target=self.__handle, args=[csock])
                t.start()

            except KeyboardInterrupt:
                # Stop listening when Ctrl+C
                self.shutdown = True
                continue
            except:
                continue

        s.close()