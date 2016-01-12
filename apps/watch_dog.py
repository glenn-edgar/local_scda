# external control 
import datetime
import time
import string
import urllib2
import math
import redis

import json
import eto
import py_cf
import os
import subprocess
import signal
import json
import base64

# devices is list of redis keys that
# contain redis keys
# the redis keys are a list of three elements
# 0 is the current time
# 1 is the pid
# 2 is the max elasped time

# to detect crash ---> check pid change

class Watch_Dog_Ctrl():
   def __init__(self, redis, directory ):
       self.redis      = redis
       self.directory  = directory
       self.pid_table  = {}
       self.redis.delete("WD_PID_TABLE")
  
   def store_alarm_queue( self, event, data ):
      log_data = {}
      log_data["event"] = event
      log_data["data"]  = data
      log_data["time" ] = time.time()

      json_data = json.dumps(log_data)
      json_data = base64.b64encode(json_data)
      self.redis.lpush( "cloud_alarm_queue", json_data)
      self.redis.ltrim( "cloud_alarm_queue", 0,800)
     
   
   def poll_devices( self, chainFlowHandle, chainObj, parameters, event ):
       print "poll devices"
       keys = self.redis.hkeys(self.directory)
       #print "keys",keys
       for i in keys:
          try:
             temp = self.redis.get( i)
             temp         = json.loads(temp)
             if temp !=  None:
                curr_time    = temp["time"] 
                max_dt       = temp["max_dt"]  
                pid          = temp["pid"]    
                description  = temp["description"]
                time_base  = time.time()
                #print "pid",pid,curr_time,int(data[2]),time_base
                if self.pid_table.has_key(i) == False:
                   self.pid_table[i] = [ pid, 0 ]
                   self.redis.hset("WD_PID_TABLE", i, 0)
                else:
                   temp = self.pid_table[i]
                   if pid != self.pid_table[i][0]  : # keep track of 
                       self.pid_table[i][0] = pid
                       self.pid_table[i][1] = self.pid_table[i][1] + 1
                       self.redis.hset("WD_PID_TABLE", i, self.pid_table[i][1])
                   if pid !=  0 :
                       max_time  = curr_time + float(max_dt)
                       #print "time_base", time_base, data[0],data[1],data[2],max_time
                       if time_base > max_time :
                           print("made it here")
                           self.store_alarm_queue( "wd_kill_process", {"index":i} )
                           os.kill( pid, signal.SIGKILL)
              
                     
          except:
            self.store_alarm_queue( "wd_exception",{"index":i} )
            print "exception  for index ",i
           


     
if __name__ == "__main__":
  
  redis = redis.StrictRedis( host = "127.1.1.1", port=6379, db = 0 )
  device_directory = "WD_DIRECTORY"
  wd = Watch_Dog_Ctrl( redis , device_directory )
  wd.store_alarm_queue( "wd_startup",None )
  #
  # Adding chains
  #
  cf = py_cf.CF_Interpreter()
  
#  
# ETO processing elements  
# 
 
  
  cf.define_chain("watch_dog_thread",True)
  cf.insert_link( "link_1","WaitTod",["*","*","*",0 ])
  cf.insert_link( "link_2","One_Step",[ wd.poll_devices ])
  cf.insert_link( "link_3","WaitTod",["*","*","*",30 ])
  cf.insert_link( "link_4","Reset",[])  


  cf.define_chain("watch_dog_queue",True)
  cf.insert_link( "link_1","WaitTod",["*","*","*",15 ])
  # add queue process routine
  #cf.insert_link( "link_2","One_Step",[ wd.poll_devices ])
  cf.insert_link( "link_3","WaitTod",["*","*","*",55 ])
  cf.insert_link( "link_4","Reset",[])  



 



  #
  # Executing chains
  #
  cf_environ = py_cf.Execute_Cf_Environment( cf )
  cf_environ.execute()



