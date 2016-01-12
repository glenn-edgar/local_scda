#!/usr/bin/env python
import pika
import json
import base64
import time
import os
import redis
import logging

global connection


class Remote_Interface_server():

   def __init__(self, redis_handle ):
     self.redis      = redis_handle
     self.cmds = {}
     self.cmds["PING"]                         = True
     self.cmds["REDIS_GET"]                    = self.redis_get
     self.cmds["REDIS_SET"]                    = self.redis_set
     self.cmds["REDIS_LLEN"]                   = self.redis_llen
     self.cmds["REDIS_LINDEX"]                 = self.redis_lindex
     self.cmds["REDIS_LSET"]                   = self.redis_lset
     self.cmds["REDIS_TRIM"]                   = self.redis_trim
     self.cmds["REDIS_PUSH"]                   = self.redis_lpush
     self.cmds["REDIS_POP"]                    = self.redis_rpop
     self.cmds["REDIS_DEL"]                    = self.redis_del
     


   def redis_get( self, command_data ):

        object_data = {}
        object_data["results"] = []
        for i in command_data:
           data = {"key":i,"data":self.redis.get(i) }
           object_data["results"].append({"key":i, "data": self.redis.get(i) } )
        return object_data

   def redis_set( self, command_data ):
        object_data = {}
        object_data["results"] = []
        for i in command_data:
           key  = i["key"]
           data = i["data"]
           self.redis.set(key,data )
        return object_data

   def redis_llen( self, command_data ):
       object_data = {}
       object_data["results"] = []
       for i in command_data:
          key = i
          object_data["results"].append({"key":i, "data":self.redis.llen(i)})
       return object_data

   def redis_lindex( self, command_data ):
       object_data = {}
       object_data["results"] = []
       for i in command_data:
          key    = i["key"]
          index  = int(i["index"])
          object_data["results"].append({"key":key, "index":index, "data":self.redis.lindex( key, index ) })
       return object_data

   def redis_lset( self, command_data ):
       object_data = {}
       object_data["results"] = []
       for i in command_data:
          key    = i["key"]
          index  = int(i["index"])
          value  = i["data"]
          self.redis.lset(key,index,value)
       return object_data

   def redis_trim( self, command_data ):
       object_data = {}
       object_data["results"] = []
       for i in command_data:
          print "i",i
          key      = i["key"]
          start    = i["start"]
          end      = i["end"]
          self.redis.ltrim(key,start, end)
    
       return object_data 

   def redis_lpush( self, command_data ):
       object_data = {}
       object_data["results"] = []
      
       for i in command_data:
            key    = i["key"]
            for j in i["data"]:
               self.redis.lpush( key, j )
      
       return object_data 

   def redis_rpop( self, command_data ):
       object_data = {}
       object_data["results"] = []

       for i in command_data:
          key    = i["key"]
          number = i["number"]
          temp1 = {"key": key,"number":number }
          temp = []
          for j in range(0,number):
              temp_1 = self.redis.rpop(key)
              if temp_1 != None:
                 temp.append(temp_1)
          temp1["data"] = temp
          object_data["results"].append(temp1)
       return object_data 

   def redis_del( self, command_data):
       object_data = {}
       object_data["results"] = []
       
       for i in command_data:
          self.redis.delete(i)
       
       return object_data




              

   def process_commands( self, command_data ):
       print "command ",command_data["command"]
       try:
            if self.cmds.has_key( command_data["command"] ) == True:
               if command_data["command"] == "PING":
                  object_data = command_data
                  object_data["reply"] = command_data["command"]
               else:
                  
                  object_data = self.cmds[ command_data["command"] ]( command_data["data"] )
                  object_data["reply"] = command_data["command"]
                  object_data["command"] = command_data["command"] 
            else:  
              object_data = {}
              object_data["reply"] = "BAD_COMMAND"
        
      
       except:
         print "exception"
         object_data = {}
         object_data["reply"] = "BAD_COMMAND"
         object_data["results"] = None
       return object_data

   def on_request(self, ch, method, props, body):
       try:
           input_data   = json.loads( base64.b64decode(body))
           print "input_data",input_data
           output_data  = self.process_commands( input_data )
           print "output_data",output_data
       except:
          print "exception"
          output_data = {}
          output_data["reply"] = "BAD_COMMAND"
          output_data["results"] = None
          output_data = json.dumps(output_data)

       #print "data output = ",output_data
       response     = base64.b64encode(  json.dumps(output_data ) )
       ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),
                     body= str(response) )
       ch.basic_ack(delivery_tag = method.delivery_tag)

     

  
if __name__ == "__main__":
   user_name = 'gedgar'
   password  = 'Gr1234gfd'
   vhost     = 'LaCima'
   queue     = 'alert_status_queue'

   logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.CRITICAL)
   redis               = redis.StrictRedis( host = "127.1.1.1", port=6379, db = 0 )
   
   command_handler = Remote_Interface_server(redis)
 
  
   credentials = pika.PlainCredentials( user_name, password )
   parameters = pika.ConnectionParameters('farmmachine.cloudapp.net',
                                                5671,  #ssl port
                                                vhost,
                                                credentials,
                                                ssl = True ,
                                                heartbeat_interval=20 )
   connection = pika.BlockingConnection(parameters)
   channel = connection.channel()
   connection.socket.settimeout(10000)
   channel.queue_delete(queue=queue)
   channel.queue_declare(queue=queue)
   channel.basic_qos(prefetch_count=1)
   channel.basic_consume( command_handler.on_request, queue=queue)
   print " [x] Awaiting RPC requests"
   channel.start_consuming()
