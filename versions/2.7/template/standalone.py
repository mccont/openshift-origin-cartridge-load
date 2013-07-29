#!/usr/bin/env python

import SocketServer
from BristleWeb import *
import socket
import time

port = 8000

def runhttpd():
    httpd = SocketServer.TCPServer(("", port), BristleWeb)
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print "serving at port", port
    httpd.serve_forever()

while(1):
   try: 
       runhttpd()
   except socket.error: 
       print "Socket ",port," in use; waiting until it should be free"
       time.sleep(15)
   except:
       pass
   else: 
       pass
   

   
