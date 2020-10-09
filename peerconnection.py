#!/usr/bin/python3
'''
Provides peer connection functions .
'''

import socket
import struct

class PeerConnection:
    """ Implements a peer connection """


    def __init__(self, host, port, sock=None):
        """ Initializes a peer connection """

        if not sock:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, int(port)))
        else:
            self.s = sock

        self.stream = self.s.makefile('rwb')


    def send(self, msgtype, msgdata=''):
        """ Sends data through the connection """

        try:
            encmsgtype = msgtype.encode('utf-8')
            encmsgdata = msgdata.encode('utf-8')
            msglen = len(encmsgdata)
            msg = struct.pack(f'!4sL{msglen}s', encmsgtype, msglen, encmsgdata)
            self.stream.write(msg)
            self.stream.flush()
        except KeyboardInterrupt:
            raise
        except:
            return False
        return True


    def receive(self):
        """ Receives data from the connection """

        try:
            msgtype = self.stream.read(4)
            if not msgtype:
                return (None, None)

            lenstr = self.stream.read(4)
            msglen = int(struct.unpack("!L", lenstr)[0])
            msg = bytearray()

            while len(msg) != msglen:
                data = self.stream.read(min(2048, msglen - len(msg)))
                if not len(data):
                    break
                msg.extend(data)

            if len(msg) != msglen:
                return (None, None)

        except KeyboardInterrupt:
            raise
        except:
            return (None, None)

        return (msgtype.decode('utf-8'), msg.decode('utf-8'))


    def close(self):
        """ Close the peer connection """

        self.s.close()
        self.s = None
        self.stream = None