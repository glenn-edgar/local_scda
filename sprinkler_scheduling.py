import os
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
import base64
import load_files



class Schedule_Monitoring():
   def __init__(self, redis ):
     self.redis         = redis
     self.app_files    =  load_files.APP_FILES(redis)



    
   def check_schedule_flag( self, schedule_name ):
      
      data =  self.redis.hget("SCHEDULE_COMPLETED", schedule_name)
 
      try:
        data = json.loads( data)

      except:
	 data = [ 0 , -3 ]

      if int(data[0]) == 0 :
         return_value = True
      else:
	 return_value = False
       
      
      return return_value
  

   def match_time( self, compare, value ):
     return_value = False
     if compare[0] < value[0]:
       return_value = True
     if (compare[0] ==  value[0]) and ( compare[1] <= value[1] ):
       return_value = True
     return return_value

   def determine_start_time( self, start_time,end_time ):
       return_value = False
       temp = datetime.datetime.today()
       st_array = [ temp.hour, temp.minute ]
       if self.match_time( start_time,end_time ) == True:
	
	  
           if ( self.match_time( start_time, st_array) and 
	        self.match_time( st_array, end_time )) == True:
	     return_value = True
       else: 

	 
	   # this is a wrap around case
	   if   self.match_time( start_time,st_array) :
              return_value = True
           if  self.match_time(st_array,end_time):
              return_value = True
       return return_value
     



   def clear_done_flag( self, *arg ):
      dow_array = [ 1,2,3,4,5,6,0]
      dow = datetime.datetime.today().weekday()
      dow = dow_array[dow]
      sprinkler_ctrl = self.app_files.load_file("sprinkler_ctrl.json")
      for  j in sprinkler_ctrl:
	  name = j["name"]
	  if self.determine_start_time( j["start_time"],j["end_time"]) == False: 
               temp_1 = json.dumps( [0,-1] )
               self.redis.hset( "SCHEDULE_COMPLETED", name,temp_1  ) 
    
  

   def check_for_active_schedule( self, *args):

      temp = datetime.datetime.today()
      dow_array = [ 1,2,3,4,5,6,0]
      dow = datetime.datetime.today().weekday()
      dow = dow_array[dow]
      st_array = [temp.hour,temp.minute]
      rain_day = self.redis.hget("CONTROL_VARIABLES" ,"rain_day" )
      try:
       rain_day = int( rain_day )
      except:
       rain_day = 0
       self.redis.set("CONTROL_VARIABLES", "rain_day", rain_day)
     
      if rain_day != 0:
	return
      sprinkler_ctrl = self.app_files.load_file("sprinkler_ctrl.json")
      for j in sprinkler_ctrl:
	  name = j["name"]
          print "checking schedule",name
          if j["dow"][dow] != 0 :
	    
            start_time = j["start_time"]
            end_time   = j["end_time"]
    
            if self.determine_start_time( start_time,end_time ):
                 print "made it past start time",start_time,end_time
                 if self.check_schedule_flag( name ):
                     print "queue in schedule ",name
                     temp = {}
                     temp["command"] =  "QUEUE_SCHEDULE"
                     temp["schedule_name"]  = name
                     temp["step"]           = 0
                     temp["run_time"]       = 0
                     scratch = json.dumps(temp)
                     self.redis.lpush("QUEUES:SPRINKLER:CTRL", base64.b64encode(scratch) )
                     temp = [1,time.time()+60*3600 ]  # +hour prevents a race condition
                     self.redis.hset( "SCHEDULE_COMPLETED",name,json.dumps(temp) ) 




class Watch_Dog_Client():
   def __init__(self, redis, directory, key, description ):
       self.redis      = redis
       self.directory  = directory
       self.key        = key
       self.description  = description
       self.redis.hset(directory,key,None)
       self.pat_wd()
   

   def pat_wd( self, *args):
       print "made it here ","key",self.key
       self.redis.delete( self.key )
       temp = {}
       temp["time"]    = time.time()
       temp["max_dt"]  = 5*60
       temp["pid"]     = os.getpid()
       temp["description"] = self.description
       self.redis.set( self.key, json.dumps(temp) )
    

if __name__ == "__main__":
  redis = redis.StrictRedis( host = "127.1.1.1", port=6379, db = 0 )
  sched = Schedule_Monitoring( redis )
  device_directory = "WD_DIRECTORY"
  wc = Watch_Dog_Client(redis, device_directory,"sprinkler_scheduling","sprinkler scheduling")
  wc.pat_wd(  )
  
  #
  # Adding chains
  #
  cf = py_cf.CF_Interpreter()
  
#  
# ETO processing elements  
# 
 
#
#
#  Time schedinging function
#
#
 

  cf.define_chain( "plc_auto_mode", True )
  cf.insert_link(  "link_1",  "One_Step", [ sched.check_for_active_schedule ] )
  cf.insert_link(  "link_2",  "WaitEvent",[ "MINUTE_TICK" ] )
  cf.insert_link(  "link_3",  "Reset",[] )
    
  cf.define_chain("clear_done_flag",True)
  cf.insert_link(  "link_2",  "One_Step", [sched.clear_done_flag ] )
  cf.insert_link(  "link_1",  "WaitEvent",[ "MINUTE_TICK" ] )
  cf.insert_link(  "link_3",  "Reset",[] )




  cf.define_chain("watch_dog_thread",True)
  cf.insert_link( "link_1","WaitTod",["*","*","*",30 ])
  cf.insert_link( "link_2","One_Step",[ wc.pat_wd ])
  cf.insert_link( "link_3","WaitTod",["*","*","*",55 ])
  cf.insert_link( "link_4","Reset",[])  


  #
  # Executing chains
  #
  
  cf_environ = py_cf.Execute_Cf_Environment( cf )
  cf_environ.execute()





