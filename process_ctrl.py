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

import subprocess    

class ProcessControl():
   def __init__(self, process_dict ):
       self.process_dict = process_dict


   def startup( self ):
       for i in self.process_dict:
           self.startup_process(i)
          
   def monitor( self ):
       for i in self.process_dict:
           self.monitor_process( i )

   def terminate( self ):
       for i in self.process_dict:
           self.terminate_process(i)

   def startup_process( self, process ):

       self.process_dict[process]["Popen"] = None
       try:
           err_file = open(self.process_dict[process]["err_file"], "wb")
           self.process_dict[process]["Popen"] = subprocess.Popen( self.process_dict[process]["args"], stderr=err_file )
           
       except Exception as e:
           print e.message, e.args
           

   def monitor_process( self, process ):
       try:
           popen = self.process_dict[process]["Popen"]
           if popen == None:
               self.startup_process(process)
           else:
               status = popen.poll()
               if status != None:
                   # TBD log error message
                   self.startup_process(process)

       except:
           self.terminate_process(process)
           self.startup_process(process)
           


   def terminate_process( self, process ):
       try:
           popen = self.process_dict[process]["Popen"]
           popen.terminate()
       except:
           print "error terminating "+process
   
  
if __name__ == "__main__":

   x = {}
   '''
   x["external_control"]                =   {} 
   x["external_control"]["args"]        =   ["python","external_control.py" ]
   x["external_control"]["err_file"]    =   "external_control.err"

   x["input_gateway"]                =   {} 
   x["input_gateway"]["args"]        =   ["python","rabbitmq_gateway.py"]
   x["input_gateway"]["err_file"]    =   "rabbitmq_gateway.err"

   x["alert_gateway"]                =   {} 
   x["alert_gateway"]["args"]        =   ["python","rabbit_alert_gateway.py"]
   x["alert_gateway"]["err_file"]    =   "rabbit_alert_gateway.err"


   x["watch_dog"]                =   {} 
   x["watch_dog"]["args"]        =   ["python","watch_dog.py"]
   x["watch_dog"]["err_file"]    =   "watch_dog.err"

   '''
   x["udp_server"]                =   {} 
   x["udp_server"]["args"]        =   ["python","python_udp_server_startup.py"]
   x["udp_server"]["err_file"]    =   "python_udp_server_startup.err"


 
  
   process_control = ProcessControl(x)
   process_control.startup()    
   while True:
     time.sleep(5)
     process_control.monitor()
   process_control.terminate()



