import re

host = 'localhost:3306'
user = 'app_user'
password = 'password'

f = open('template_rw.xml','r')

for line in f:
    line = re.sub(r"@@HOSTREF@@",host,line)
    line = re.sub(r"@@USER@@",user,line)
    line = re.sub(r"@@PASSWORD@@",password,line)
    print line

print "Starting a load for %s@%s on %s" % (user,password,host)
