import cgi, os, SocketServer, sys, time, urllib
from SimpleHTTPServer import SimpleHTTPRequestHandler
from StringIO import StringIO
import urlparse
from types import *
import re
import signal
import mimetypes
import json
import collections

child_processes = []

allreads = {}
allwrites = {}
counter = 0
records = 0
currmsg = ''
activehostname = 'No active process'

coreconfig = { 'core' : { 'testDuration' : 1200,
                          'autoCommit': 'false',
                          'statusInterval': 500,
                          'csvFile': "results.out",
                          'separator' : ',',
                          'name' : 'dynamic',
                          },
               'connback' : {'urlprefix' : 'jdbc:mysql://',
                             'urlsuffixrw' : '/evaluator@qos=RW_STRICT&amp;createDatabaseIfNotExist=true&amp;autoReconnect=true',
                             'urlsuffixro' : '/evaluator@qos=RO_RELAXED&amp;autoReconnect=true',
                             'host' : 'localhost:3306',
                             },

               'conn' : { 'name' : 's1',
                          'driver' : 'com.mysql.jdbc.Driver',
                          'url' : 'jdbc:mysql://localhost:3306/evaluator@qos=RO_RELAXED&amp;autoReconnect=true',
                          'user' : 'tungsten',
                          'password' : 'secret',
                          },
               'tabgroup' : { 'name' : 'ta',
                              'size' : 100,
                              'dataSource' : 's1',
                              },
               'thrgrouprw' : { 'name' : 'A',
                                'dataSource' : 's2',
                                'threadCount' : 10,
                                'thinkTime' : 10,
                                'updates' : 50,
                                'deletes' : 0,
                                'inserts' : 0,
                                'readSize' : 1,
                                'rampUpInterval' : 5,
                                'rampUpIncrement' : 5,
                                'reconnectInterval' : 10,
                                },
               'thrgroupro' : { 'name' : 'B',
                                'dataSource' : 's1',
                                'threadCount' : 30,
                                'thinkTime' : 10,
                                'readSize' : 1,
                                'rampUpInterval' : 5,
                                'rampUpIncrement' : 5,
                                'reconnectInterval' : 10,
                                },
               }

def parsefile(infile,outfile,vars):
      host = 'localhost:3306'
      user = 'app_user'
      password = 'password'

      if 'conn' in vars:
            if 'host' in vars['conn']:
                  print "Got the host from the client"
                  host = vars['conn']['host']
                  password = vars['conn']['password']
                  user = vars['conn']['user']

      (realhost,hostport) = host.split(':')

      global activehostname
      activehostname = " %s, Port: %s, User: %s, Password: %s" % (realhost,hostport,user,password)

      f = open(infile,'r')
      o = open(outfile,'w')

      for line in f:
            line = re.sub(r"@@HOSTREF@@",host,line)
            line = re.sub(r"@@REALHOST@@",realhost,line)
            line = re.sub(r"@@HOSTPORT@@",hostport,line)
            line = re.sub(r"@@USER@@",user,line)
            line = re.sub(r"@@PASSWORD@@",password,line)
            o.write(line)

# Construct an XML tag with the tagname
# Keys are taken from the coreconfig structure
# But values are read from the supplied 'attributes' dictionary if they exist

def writexml(tagname,coreattr,attributes,content):
      tag = StringIO()
      tag.write('<%s '%(tagname))
      for k,v in coreattr.iteritems():
            if k in attributes: 
                  tag.write('%s="%s" '%(k,str(attributes[k])))
            else:
                  tag.write('%s="%s" '%(k,str(v)))
      if content:
            tag.write('>%s</%s>'%(content,tagname))
      else:
            tag.write('/>')
      return tag.getvalue();

def write_bc_config(filename,vars):
      conf = open(filename,'w')
      conf.write('<!DOCTYPE EvaluatorConfiguration SYSTEM "file://../xml/evaluator.dtd">')

      connlist = ''
      
      if 'conn' in vars: 
            vars['conn']['url'] = coreconfig['connback']['urlprefix'] + vars['conn']['host'] + coreconfig['connback']['urlsuffixro']
            connlist = writexml('DataSource',coreconfig['conn'],vars['conn'],None)
      else:
            connlist = writexml('DataSource',coreconfig['conn'],{'name' : 's1'},None)

      if 'rosettings' in vars:
            thgroups = writexml('ThreadGroup',coreconfig['thrgroupro'],vars['rosettings'],None)
      else:
            thgroups = writexml('ThreadGroup',coreconfig['thrgroupro'],coreconfig['thrgroupro'],None)

      if ('connections' in vars):
            if int(vars['connections']) == 2:
                  print "Writing a R/W connection"
                  newconn = {}
                  if 'conn' in vars:
                        newconn = vars['conn']
                        newconn['url'] = coreconfig['connback']['urlprefix'] + vars['conn']['host'] + coreconfig['connback']['urlsuffixrw']
                  else:
                        newconn = coreconfig['conn']
                        newconn['url'] = coreconfig['connback']['urlprefix'] + coreconfig['connback']['host'] + coreconfig['connback']['urlsuffixrw']
                  newconn['name'] = 's2'
                  
                  connlist += writexml('DataSource',coreconfig['conn'],newconn,None)

                  if 'rwsettings' in vars:
                        thgroups += writexml('ThreadGroup',coreconfig['thrgrouprw'],vars['rwsettings'],None)
                  else:
                        thgroups += writexml('ThreadGroup',coreconfig['thrgrouprw'],coreconfig['thrgrouprw'],None)

      conf.write(writexml('EvaluatorConfiguration',
                          coreconfig['core'],coreconfig['core'],
                          connlist + 
                          writexml('TableGroup',coreconfig['tabgroup'],coreconfig['tabgroup'],
                                   thgroups
                                   )
                          )
                 )

def parselog():
    logfile = 'current.log'
    currmsg = 'Starting...'

    try: 
          f = open(logfile,'r')
    except: 
          currmsg = 'Load started; no data yet'
          return

    global allreads, allwrites

    allreads = {}
    allwrites = {}

    for line in f:
        results = line.split(',')

        if (len(results) >= 13):
            time = results[1]
            selects = results[3]
            updates = results[9]
            deletes = results[11]
            inserts = results[13]
            reads = int(float(selects))
            writes = int(float(updates) + float(deletes) + float(inserts))
            realtime = re.match(r'\d+\s+INFO\s+(\d+)',time)

            print "R: ",reads, " W: ",writes
            
            seconds = int(int(realtime.group(1))/1000)

            if seconds in allreads:
                allreads[seconds] += reads
                allwrites[seconds] += writes
            else:
                allreads[seconds] = reads
                allwrites[seconds] = writes

def logasjson():
    outputcount = 0
    basecounter = 0
    reads = []
    writes = []
    global currmsg
    global allreads,allwrites

    od = collections.OrderedDict(sorted(allreads.items()))

    for rec in od.iteritems():
        (seconds,readval) = rec
        reads.append([seconds,allreads[seconds]])
        writes.append([seconds,allwrites[seconds]])
        outputcount = outputcount+1

    if (outputcount > 0):
          currmsg = 'Displaying data'
    else:
          currmsg = 'Bristlecone starting; no data yet'

    return json.dumps({'reads': reads, 
                       'writes': writes, 
                       'counter': outputcount, 
                       'hostname' : activehostname,
                       'datastatus': currmsg})

class BristleWeb(SimpleHTTPRequestHandler):
      mimetypes.init()
      counter = 0
      records = {}

      def do_GET(self):
          parsed_path = urlparse.urlparse(self.path)
          qs = urlparse.parse_qs(parsed_path.query)

          if ((len(qs) > 0) & ('m' in qs)):
             if qs['m'] == ['data']:
                 self.parselog()

             if qs['m'] == ['stop']:
                 print "Stopping known child processes"
                 for pid in child_processes:
                     try:
                         os.killpg(pid,signal.SIGKILL)
                     except Exception: 
                         pass
                     self.send_response(200)
                     self.send_header('Content-type', 'application/json')
                     self.end_headers()
                     self.wfile.write('{msg: "Load stopped for " + child_pid, pid: child_pid }')

             if qs['m'] == ['load']:
                   parselog()
                   self.send_response(200)
                   self.send_header('Content-type', 'application/json')
                   self.end_headers()
                   self.wfile.write(logasjson())

             if qs['m'] == ['start']:
                   vars = { 'host' : 'localhost:3306',
                            'user' : 'tungsten',
                            'password' : 'secret',
                            }
                   if 'vars' in qs: 
                         print "Got : ",str(qs['vars'][0])
                         vars = json.loads(str(qs['vars'][0]))

                   print "Starting load..."
# First rewrite the execution script
                   parsefile('template_load.sh','start_load.sh',vars)
# Now rewrite the configuration file to initialize
                   parsefile('template_create.xml','create_tables.xml',vars)
# Now rewrite the configuration file to run
#                 parsefile('template_rw.xml','load_config.xml',vars)
                   write_bc_config('load_config.xml',vars)

# We fork the process that runs bristlecone
                   print "Starting an external process with the data"
                   print "Starting a load for %s@%s on %s" % (vars['conn']['user'],vars['conn']['password'],vars['conn']['host'])
                   
                   child_pid = os.fork()
                   if child_pid == 0:
                         os.execl('start_load.sh','load_tester');
                   else:
                         child_processes.append(child_pid)
                         self.send_response(200)
                         self.send_header('Content-type', 'application/json')
                         self.end_headers()
                         self.wfile.write('{msg: "Starting load for " + child_pid, pid: child_pid }')

          else:
             filetoserve = parsed_path.path[1:]

             if (len(filetoserve) == 0): 
                 filetoserve = 'index.htm'

             try: 
                  f = open(filetoserve,'r')
             except: 
                  self.send_response(404)
             else:
                 self.send_response(200)
                 (type,encoding) = mimetypes.guess_type(filetoserve)
                 self.send_header('Content-type',type)
                 self.end_headers()
                 for line in f:
                     self.wfile.write(line)