import pika
import uuid
import redis
import time
import os
import base64

class rpc_control_client(object):
    def __init__(self,user,password,host,v_host, queue  ):
        self.queue = queue
        self.credentials = pika.PlainCredentials( user, password)
        self.parameters = pika.ConnectionParameters('farmmachine.cloudapp.net',
                                       5671,
                                       vhost,
                                       self.credentials,
                                       ssl = True )

        self.connection = pika.BlockingConnection( self.parameters)
        self.channel = self.connection.channel()
        
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)



    def on_response(self, ch, method, props, body):
        print "got response"
        if self.corr_id == props.correlation_id:
           self.response = body



    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(n))
        self.timeout = 100 # wait 10 seconds
        while self.response is None:
            self.connection.process_data_events()
            if self.response is not None:
               return [ True, int(self.response) ]
            self.timeout = self.timeout -1
            if self.timeout == 0:
               return [ False ]
            else:
              time.sleep(.1) 

               
        return int(self.response)



test_rpc = rpc_control_client('gedgar','Gr1234gfd','farmmachine.cloudapp.net','LaCima','rpc_queue'  )

for i in range(0,30):
  response = test_rpc.call(30)
  print "i",i
  print "time",time.time()
  print " [.] Got %r" % (response,)
