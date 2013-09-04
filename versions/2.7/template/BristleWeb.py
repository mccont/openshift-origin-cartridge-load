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
import stat
from time import *

child_processes = []

windowsize = 100
allreads = {}
allwrites = {}
reads = []
writes = []
counter = 0
records = 0
lastseconds = 0
runcount = 0
currmsg = ''
currstatus = 'idle'
runstatus = ''
activehostname = 'No active process'
fakingit = 0
fakeseconds = 0

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
                              'size' : 1000,
                              'dataSource' : 's1',
                              },
               'thrgrouprw' : { 'name' : 'A',
                                'dataSource' : 's2',
                                'threadCount' : 150,
                                'thinkTime' : 100,
                                'updates' : 60,
                                'deletes' : 0,
                                'inserts' : 0,
                                'readSize' : 10,
                                'rampUpInterval' : 1,
                                'rampUpIncrement' : 100,
                                'reconnectInterval' : 10,
                                },
               'thrgroupro' : { 'name' : 'B',
                                'dataSource' : 's1',
                                'threadCount' : 330,
                                'thinkTime' : 200,
                                'readSize' : 1000,
                                'rampUpInterval' : 1,
                                'rampUpIncrement' : 150,
                                'reconnectInterval' : 10,
                                },
               }

def parsefile(infile,outfile,vars):
      host = 'localhost:3306'
      user = 'app_user'
      password = 'password'

      if 'conn' in vars:
            if 'host' in vars['conn']:
                  host = vars['conn']['host']
                  password = vars['conn']['password']
                  user = vars['conn']['user']

      (realhost,hostport) = host.split(':')

      global activehostname
      activehostname = " %s:%s" % (realhost,hostport)

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
                          coreconfig['core'],vars['core'],
                          connlist + 
                          writexml('TableGroup',coreconfig['tabgroup'],coreconfig['tabgroup'],
                                   thgroups
                                   )
                          )
                 )

def parselog():
    logfile = 'current.log'
    global currmsg
    global currstatus
    global runstatus
    global lastseconds
    global runcount
    global windowsize
    currmsg = 'Starting...'
    currstatus = 'active'

    try: 
          f = open(logfile,'r')
    except: 
          currmsg = 'Load started; no data yet'
          return

    global allreads, allwrites

    allreads = {}
    allwrites = {}

    lastseconds = 0

    linesprocessed = 0
    runcount = 0

    for line in f:
          if re.search(r"Can't connect to MySQL server",line):
                currstatus = 'error'
                currmsg = 'Cannot connect to MySQL server'
                print "MySQL Connection error; returning that"
                return

          if re.search(r"Test run complete",line):
                currstatus = 'finished'
                runcount = runcount + 1
                if (lastseconds != 0):
                      del(allreads[lastseconds])
                      del(allwrites[lastseconds])
                if (len(allreads) > 0): 
                      if (windowsize > len(allreads)):
                            windowsize = int(len(allreads)/2)

          match = re.search(r"STATUS:\s+(.*)",line)
          if (match):
                currstatus = 'active'
                currmsg = match.group(1)
                runstatus = match.group(1)

          match = re.search(r"com.continuent.bristlecone.evaluator.EvaluatorException:\s+(.*)",line)
          if (match):
                currstatus = 'active'
                currmsg = match.group(1)
                runstatus = match.group(1)

          if re.search(r"\d+\s+INFO\s+\d+",line):

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

                    currstatus = 'active'
                    currmsg = 'Showing live data'
                
                    if (runcount > 2):
                          currmsg = 'Showing live data (iteration %d)'%(runcount)

                    seconds = int(int(realtime.group(1))/1000)

                    if seconds in allreads:
                          linesprocessed = linesprocessed + 1
                          allreads[seconds] += reads
                          allwrites[seconds] += writes
                    else:
                          linesprocessed = linesprocessed + 1
                          allreads[seconds] = reads
                          allwrites[seconds] = writes

                    lastseconds = seconds

#    print "Loaded seconds from logfile: ",lastseconds
#    print "Got ",strftime("%H:%M:%S",localtime(lastseconds))

# If the test run has completed, then the last line is actually a summary
# line and it needs to be ignored

# Extract a window of data using start/end points

def populatedata(start,stop):
      global allreads,allwrites
      global reads,writes

      pointer = -1

      od = collections.OrderedDict(sorted(allreads.items()))

      for rec in od.iteritems():
            pointer = pointer + 1
# Skip to the start of the records we want to extract
            if (pointer < start):
                  continue
            if (pointer >= stop):
                  break
            (seconds,value) = rec
            reads.append([seconds*1000,allreads[seconds]])
            writes.append([seconds*1000,allwrites[seconds]])

# We can calculate the range of items to put in the window on the data 

# If the number of data items read < windowsize

# The range is: 
# start to datasize

# If the number of data items read > windowsize

# The range is: 
# skipstart-windowsize to skipstart + windowsize

# If the number of data items read > windowsize and skipstart > windowsize

# The range is: 
# skipstart-windowsize to datasize + 0 to windowsize - displayed items
                         
def logasjson(skipbase):
     global currmsg,currstatus
     global allreads,allwrites
     global reads,writes
     global windowsize
     reads = []
     writes = []

     datasize = len(allreads)

# Base calculation, either we display all records from 0 to datasize
# or we display from the skip point to end of the data

# Not enough data, just display what we have

     if (datasize < windowsize):
           populatedata(0,datasize)
     elif (datasize >= windowsize):
           populatedata((datasize-windowsize),datasize)

     return json.dumps({'reads' : reads, 
                        'writes' : writes, 
                        'datainlog' : len(allreads),
                        'dataingraph' : len(reads),
                        'windowsize' : windowsize,
                        'hostname' : activehostname,
                        'status' : currstatus,
                        'currmsg' : currmsg})

class BristleWeb(SimpleHTTPRequestHandler):
      global allreads,allwrites
      global windowsize
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
                 child_pid = os.fork()
                 if child_pid == 0:
                       os.execl('stop_load.sh','load_tester');
                 else:
                       self.send_response(200)
                       self.send_header('Content-type', 'application/json')
                       self.end_headers()
                       self.wfile.write(json.dumps({'datastatus' : "Load stopped"}))

             if qs['m'] == ['load']:
                   parselog()
                   self.send_response(200)
                   self.send_header('Content-type', 'application/json')
                   self.end_headers()
                   self.wfile.write(logasjson(int(qs['skip'][0])))

             if qs['m'] == ['start']:
                   windowsize = 100
                   try: 
                         os.remove('current.log')
                   except:
                         pass

                   allreads = ()
                   allwrites = ()

                   vars = { 'host' : 'localhost:3306',
                            'user' : 'tungsten',
                            'password' : 'secret',
                            }
                   if 'vars' in qs: 
                         vars = json.loads(str(qs['vars'][0]))

                   fakingit = 0

# First rewrite the execution script
                   parsefile('template_load.sh','start_load.sh',vars)
                   os.chmod('start_load.sh',stat.S_IRWXG|stat.S_IRWXU|stat.S_IRWXO)

# Now rewrite the configuration file to initialize
                   parsefile('template_create.xml','create_tables.xml',vars)

# Now rewrite the configuration file to run
                   write_bc_config('load_config.xml',vars)

                   print "Stopped any existing loads"
                   os.system('./stop_load.sh')

# We fork the process that runs bristlecone
                   print "Starting a load for %s@%s on %s" % (vars['conn']['user'],vars['conn']['password'],vars['conn']['host'])
                   
                   child_pid = os.fork()
                   if child_pid == 0:
                         os.execl('start_load.sh','load_tester');
                         print "Started load test script"
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
