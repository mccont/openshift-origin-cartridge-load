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

child_processes = []

allreads = {}
allwrites = {}
counter = 0
records = 0
lastseconds = 0
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
                          coreconfig['core'],coreconfig['core'],
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

    for line in f:
          if re.search(r"Can't connect to MySQL server",line):
                currstatus = 'error'
                currmsg = 'Cannot connect to MySQL server'
                print "MySQL Connection error; returning that"
                return

          match = re.search(r"STATUS:\s(.*?)",line)
          if (match):
                currstatus = 'active'
                currmsg = match.group(0)
                runstatus = match.group(0)

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

# If the test run has completed, then the last line is actually a summary
# line and it needs to be ignored

          if linesprocessed > 600:
                if re.search(r'Test run complete',line):
                      del allreads[lastseconds]
                      del allwrites[lastseconds]


def logasjson(skipbase):
    outputcount = 0
    basecounter = 0
    reads = []
    writes = []
    global currmsg,currstatus
    global allreads,allwrites
    global fakingit
    global fakeseconds
    global lastseconds
    windowsize = 150
    skipstart = (skipbase % len(allreads))

    print "Starting data output at ",skipstart

    od = collections.OrderedDict(sorted(allreads.items()))

    for rec in od.iteritems():
          basecounter = basecounter+1
          if basecounter <= skipstart: 
                continue
          (seconds,readval) = rec
          if not fakingit:
                fakeseconds = seconds
          reads.append([(fakeseconds*1000),allreads[seconds]])
          writes.append([(fakeseconds*1000),allwrites[seconds]])
          if fakingit:
                fakeseconds = fakeseconds + 2
          outputcount = outputcount+1
          if outputcount >= windowsize:
                break

    if (currstatus == 'active'):
          if (outputcount > 0):
                currmsg = 'Live data showing'

# If the output count starts reducing from the windowsize
# We fake the output by just looping round the material again, but 
# update the display status to show that the stats are cached, rather
# than new information

    print "End of initial, total records: %d, outputcount: %d, windowsize: %d, skipstart: %d"%(len(allreads),outputcount,windowsize,skipstart)

    if ((outputcount < windowsize) and
        (skipstart > windowsize)):
          print "Warning: We gotta loop the info round again, starting at ",lastseconds
          currmsg = 'Cached data showing'
          fakingit = 1

          for rec in od.iteritems():
                (seconds,readval) = rec

# If we're going round again, we're automatically into fake second territory

                reads.append([(fakeseconds*1000),allreads[seconds]])
                writes.append([(fakeseconds*1000),allwrites[seconds]])
                fakeseconds = fakeseconds + 2
                fakesecdiff = seconds
                outputcount = outputcount+1
                if outputcount >= windowsize:
                      break

    print "Records in output: ",len(reads)

    return json.dumps({'reads': reads, 
                       'writes': writes, 
                       'counter': outputcount, 
                       'hostname' : activehostname,
                       'status' : currstatus,
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
                   vars = { 'host' : 'localhost:3306',
                            'user' : 'tungsten',
                            'password' : 'secret',
                            }
                   if 'vars' in qs: 
                         vars = json.loads(str(qs['vars'][0]))

                   fakingit = 0

                   print "Starting load..."
# First rewrite the execution script
                   parsefile('template_load.sh','start_load.sh',vars)
                   os.chmod('start_load.sh',stat.S_IRWXG|stat.S_IRWXU|stat.S_IRWXO)
# Now rewrite the configuration file to initialize
                   parsefile('template_create.xml','create_tables.xml',vars)
# Now rewrite the configuration file to run
                   write_bc_config('load_config.xml',vars)

# We fork the process that runs bristlecone
                   print "Starting an external process with the data"
                   print "Starting a load for %s@%s on %s" % (vars['conn']['user'],vars['conn']['password'],vars['conn']['host'])

                   try: 
                         os.remove('current.log')
                   except:
                         pass
                   
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
