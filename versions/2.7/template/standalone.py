#!/usr/bin/env python

import SocketServer
from BristleWeb import *
import socket
import time
import os

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
   except NameError as e:
       print "Some other exception occurred: ",e
   except:
       os.system("./stop_load.sh")
       os.wait()
       print "Some other exception occurred: ",sys.exc_info()[0]
       time.sleep(30)
       pass
   else: 
       pass
   

   
