#!/usr/bin/python3
'''
Message helper class .
'''


class Message:
    """ Implements the message class """


    def __init__(self, iscallable, isasync, helper):
        """ Initializes a message """

        self.iscallable = iscallable
        self.isasync = isasync
        self.helper = helper

    def addHandler(self, handler):
        """ Adds a handler to the message """
        self.handler = handler
        return self


messages = {
    'PING': Message(True, False, "Pings another peer"),
    'ECHO': Message(True, False, "Echoes a message"),
    'FIND': Message(False, False, "Finds a peer on the P2P network"),
    'ASYN': Message(True, True, "Requests an echo message"),
    'ARES': Message(False, False, "Handles the echo response")
}