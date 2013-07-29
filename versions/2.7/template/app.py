#!/usr/bin/env python
import imp
import os
import sys
from BristleWeb import *
import SocketServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import time
import socket

try:
   zvirtenv = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'],
                           'virtenv', 'bin', 'activate_this.py')
   execfile(zvirtenv, dict(__file__ = zvirtenv) )
except IOError:
   pass


def run_simple_httpd_server(ip, port=8080):
   httpd = SocketServer.TCPServer((str(ip), int(port)), BristleWeb)
   print "serving at port", port, "IP ",ip
   httpd.serve_forever()   


#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
# 


#
#  main():
#
if __name__ == '__main__':
   ip   = os.environ['OPENSHIFT_PYTHON_IP']
   port = int(os.environ['OPENSHIFT_PYTHON_PORT'])
   zapp = imp.load_source('application', 'wsgi/application')

   #  Use gevent if we have it, otherwise run a simple httpd server.
   print 'Starting SimpleHTTPServer on %s:%d ... ' % (ip, port)
   try: 
       run_simple_httpd_server(ip, port)
   except socket.error: 
       print "Socket in use; waiting until it should be free"
       time.sleep(15)
   except: 
       pass
   else: 
       pass

