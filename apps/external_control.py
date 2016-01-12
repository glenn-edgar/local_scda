# external control 
import datetime
import time
import string
import urllib2
import math
import redis
import base64
import json
import eto
import py_cf
import os
#import sys  # Need to have acces to sys.stdout
#fd = open('/media/mmc1/python/eto_debug.out.debug','a+') # open  
#old_stdout = sys.stdout   # store the default system handler to be able to restore it
#sys.stdout = fd # Now your file is used by print as destination 
#fd.write( "this is a debug print \n"3)
#fd.write( "this is a debug print \n" )



class Eto_Management():
   def __init__(self, redis ):
       self.redis = redis
       self.sites = sites = [ "MSRUC1", #SANTA ROSA PLATEAU CA US, Temecula, CA
                              "MECSC1", #EL CARISO CA US, Lake Elsinore, CA
                              "MCSPC1"  #CSS CASE SPRINGS CA US, Murrieta, CA 
                             ]
       self.alt = 2400
      

   def calculate_daily_eto( self, chainFlowHandle, chainObj, parameters, event ):
        print datetime.datetime.now()
        print("calculating yesterday eto")
        eto_data = eto.determine_yesterday_eto(self.redis, self.sites, self.alt)
        print("eto_data",eto_data)
        #self.redis.set("YESTERDAY_ETO", eto_data )
        #if int(self.redis.get("YESTERDAY_UPDATE_FLAG")) == 1 :
        self.redis.set("YESTERDAY_ETO", eto_data )
        self.update_sprinklers_time_bins( eto_data )
        #self.redis.set("YESTERDAY_UPDATE_FLAG",0)
        self.store_event_queue( "store_eto", eto_data) 
           
   def update_sprinklers_time_bins( self, yesterday_eto ):  
        list_string = self.redis.get( "ETO_RESOURCE_LIST" )
        list_data = string.split(list_string,":")
        for j in list_data:
	     try:
               temp = self.redis.get(  j )
               temp = float(temp)             
             except: 
	       temp = 0
             temp = temp + yesterday_eto
             if temp > .3 :
               temp = .3
             self.redis.set(  j, temp )
 

   def store_event_queue( self, event, data ):
          log_data = {}
          log_data["event"] = event
          log_data["data"]  = data
          log_data["time"]  = time.time()
          json_data = json.dumps(log_data)
          json_data = base64.b64encode(json_data)
          self.redis.lpush( "cloud_event_queue", json_data)
          self.redis.ltrim( "cloud_event_queue", 0,800)
 

   def calculate_current_eto( self, chainFlowHandle, chainObj, parameters, event ):
        print( "calculating eto \n")
        try:
          eto_data = eto.calculate_current_eto( self.sites, self.alt)
          print( "current eto",(eto_data["net_et"],"\n")) 
          self.store_event_queue( "store_eto", eto_data )
          self.redis.set("CURRENT_ETO", eto_data["net_et"] )
          self.redis.set("CURRENT_ETO_DATA",eto_data)
          print("updating eto \n")
        except: 
          fd.write("exception in calculating eto \n")
          self.redis.set("CURRENT_ETO", 0 )
          self.redis.set("CURRENT_WIND_GUST", 0)
          self.redis.set("CURRENT_WIND_GUST_TIME_STAMP", 0)
          self.redis.set("CURRENT_ETO_DATA", 0)  
          self.store_event_queue( "store_eto_exception", eto_data["net_et"] ) 

   def  do_house_keeping( self, chainFlowHandle, chainObj, parameters, event ):
          pass
          #self.redis.set( "YESTERDAY_UPDATE_FLAG", 1 )


   def delete_email_files( self,chainFlowHandle, chainOjb, parameters, event ):  
       print( str(datetime.datetime.now())+"\n")
       print("deleteing emails \n")
       eto.delete_email()   

   def restart( self,chainFlowHandle, chainOjb, parameters, event ):  
       pass   



class Ntpd():
   def __init__( self ):
     pass

   def get_time( self, chainFlowHandle, chainObj, parameters, event ):
     os.system("ntpdate -b -s -u pool.ntp.org")

class Watch_Dog_Client():
   def __init__(self, redis, directory, key, description ):
       self.redis      = redis
       self.directory  = directory
       self.key        = key
       self.description  = description
       self.redis.hset(directory,key,None)
       self.pat_wd( None, None, None, None)
   

   def pat_wd( self, chainFlowHandle, chainObj, parameters, event ):
       self.redis.delete( self.key )
       temp = {}
       temp["time"]    = time.time()
       temp["max_dt"]  = 5*60
       temp["pid"]     = os.getpid()
       temp["description"] = self.description
       self.redis.set( self.key, json.dumps(temp) )
    
     
if __name__ == "__main__":
  
  redis = redis.StrictRedis( host = "127.1.1.1", port=6379, db = 0 )
  etm = Eto_Management( redis )
  #etm.calculate_daily_eto( None,None,None,None)
  print( "made it here on startup")
  #etm.calculate_daily_eto( None,None,None,None)
  #etm.delete_email_files( None, None, None, None )
  ntpd = Ntpd()
  device_directory = "WD_DIRECTORY"
  wc = Watch_Dog_Client(redis, device_directory,"extern_ctrl","external control")
  wc.pat_wd( None, None, None, None )
  #
  # Adding chains
  #
  cf = py_cf.CF_Interpreter()
  
#  
# ETO processing elements  
# 
#  cf.define_chain( "master_sequencer", True )    ## auto start thread 
#  cf.insert_link( "link_3", "Enable_Chain",[["new_day_house_keeping","get_current_eto","delete_cimis_email_data" ]])
#  cf.insert_link( "link_4","Disable_Chain",[["master_sequencer"]]) 

  cf.define_chain("get_current_eto",True)
  cf.insert_link( "link_1", "WaitTod", ["*",12, "*","*" ] )
  cf.insert_link( "link_2", "One_Step", [etm.calculate_daily_eto ] )
  cf.insert_link( "link_3", "WaitTod", ["*",13,"*","*" ] )
  cf.insert_link( "link_4", "Reset", [] )


  cf.define_chain("delete_cimis_email_data",True)
  cf.insert_link( "link_1","WaitTod",["*",14,"*","*" ])
  cf.insert_link( "link_2","One_Step",[etm.delete_email_files])
  cf.insert_link( "link_3","WaitTod",["*",15,"*","*" ])
  cf.insert_link( "link_4","Reset",[])  





#  cf.define_chain("new_day_house_keeping",False)
#  cf.insert_link( "link_1","WaitTod",["*",12,"*","*" ])
#  cf.insert_link( "link_2","One_Step",[etm.do_house_keeping])
#  cf.insert_link( "link_3","WaitTod",["*",13,"*","*" ])
#  cf.insert_link( "link_4","Reset",[])
#
#  cf.define_chain("get_current_eto",False)
#  cf.insert_link( "link_1", "WaitTod", ["*",12, 20,"*" ] )
#  cf.insert_link( "link_2", "One_Step", [etm.calculate_current_eto ] )
#  cf.insert_link( "link_3", "One_Step", [etm.calculate_daily_eto ] )
#  cf.insert_link( "link_4", "WaitTod", ["*",13,50,"*" ] )
#  cf.insert_link( "link_5", "Reset", [] )
# 
 
 

#
#
# internet time update
#
#
  
  cf.define_chain("ntpd",True)
  cf.insert_link( "link_9","Log",["ntpd"] )
  cf.insert_link(  "link_1",  "One_Step", [ntpd.get_time] )
  cf.insert_link(  "link_10", "Log",["got time"] )
  cf.insert_link(  "link_2",  "WaitEvent",[ "HOUR_TICK" ] )
  cf.insert_link(  "link_3",  "Reset",[] )
#
#
# update clocks from internet
#
#

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



