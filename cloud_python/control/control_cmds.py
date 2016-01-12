import json



class Remote_Interface_Client():
   def __init__(self ):
       pass  # place holder for now

   def ping( self ):
     temp = {}
     temp["cmd"] = "PING"
     return json.dumps(temp)

   def set_offline( self ):
     temp = {}
     temp["cmd"] = "OFFLINE"
     return json.dumps(temp)

  def restart_program( self ):
     temp = {}
     temp["cmd"]         = "RESTART_PROGRAM"
     return json.dumps(temp)

  def reboot_system( self ):
     temp = {}
     temp["cmd"]         = "REBOOT_SYSTEM"
     return json.dumps(temp)

  def clean_filter( self ):
     temp = {}
     temp["cmd"]         = "CLEAN_FILTER"
     return json.dumps(temp)

  def open_master_valve( self ):
     temp = {}
     temp["cmd"]         = "OPEN_MASTER_VALVE"
     return json.dumps(temp)


  def close_valve( self ):
     temp = {}
     temp["cmd"]         = "CLOSE_VALVE"
     return json.dumps(temp)


  def set_auto_mode( self ):
     temp = {}
     temp["cmd"]         = "AUTO_MODE"
     return json.dumps(temp)


  def queue_schedule( self, schedule ):
     temp = {}
     temp["cmd"]         = "QUEUE_SCHEDULE"
     temp["schedule"]    = schedule
     return json.dumps(temp)


  def queue_schedule_step( self, schedule, step ):
     temp = {}
     temp["cmd"]         = "QUEUE_SCHEDULE_STEP"
     temp["schedule"]    = schedule
     temp["step"]        = step
     return json.dumps(temp)


  def queue_schedule_step_time( self, schedule, step, time ):
     temp = {}
     temp["cmd"]         = "QUEUE_SCHEDULE_STEP_TIME"
     temp["schedule"]    = schedule
     temp["step"]        = step
     temp["time"]        = time
     return json.dumps(temp)


  def turn_on_valve( self, controller, valve, time ):
     temp = {}
     temp["cmd"]          = "TURN_ON_VALVE"
     temp["controller"]   = controller
     temp["valve"]        = valve
     return json.dumps(temp)


  def turn_off_valve( self ): #same of
     temp = {}
     temp["cmd"] = "TURN_OFF_VALVE"
     return json.dumps(temp)
   


class Remote_Interface_server():

   def __init__(self, redis_handle ):
     self.redis = redis_handle
     self.cmds = {}
     self.cmds["PING"]                        = self.ping
     self.cmds["AUTO_MODE"]                   = self.auto
     self.cmds["OFFLINE"]                     = self.set_offline
     self.cmds["RESTART_PROGRAM"]             = self.restart_program
     self.cmds["REBOOT_SYSTEM"]               = self.reboot_system
     self.cmds["CLEAN_FILTER"]                = self.clean_filter
     self.cmds["OPEN_MASTER_VALVE"]           = self.open_master_valve
     self.cmds["CLOSE_VALVE"]                 = self.close_valve
     self.cmds["AUTO_MODE"]                   = self.set_auto_mode
     self.cmds["QUEUE_SCHEDULE"]              = self.queue_schedule
     self.cmds["QUEUE_SCHEDULE_STEP"]          = self.queue_schedule_step
     self.cmds["QUEUE_SCHEDULE_STEP_TIME"]    = self.queue_schedule_step_time
     self.cmds["TURN_ON_VALVE"]               = self.turn_on_valve
     self.cmds["TURN_OFF_VALVE"]              = self.turn_off_valve
   

   def parse_command( self, command_data ):
      try:
         command_object = json.loads( command_data )
         if self.cmds.has_key( command_object["cmd"] ):
             return json.dumps( self.cmds[ command_object["cmd"] ]( command_object ) )
         else:
            bad_command = {}
            bad_command["reply"] = "BAD_COMMAND"
            bad_command["bad_data"] = command_data
            return json.dumps(bad_command)     
      except:
          bad_command = {}
          bad_command["reply"] = "BAD_FORMAT"
          bad_command["bad_data"] = command_data
          return json.dumps(bad_command )
       
   def ping( self, object_data ):
         object_data["reply"] = "PING"
         return object_data
     
     

   def set_offline( self, object_data ):
          object_data["reply"] = "OFFLINE"
          self.redis.set( "sprinkler_ctrl_mode","OFFLINE")
          self.redis.lpush( "sprinkler_ctrl_queue","QUEUE_SCHEDULE")


  def restart_program( self, object_data ):
          object_data["reply"] = "RESTART_PROGRAM"
          self.redis.set( "sprinkler_ctrl_mode","RESTART_PROGRAM")
          self.redis.lpush( "sprinkler_ctrl_queue","RESTART_PROGRAM")


  def reboot_system( self, object_data ):
          object_data["reply"] = "RESET_SYSTEM"
          self.redis.set( "sprinkler_ctrl_mode","RESET_SYSTEM")
          self.redis.lpush( "sprinkler_ctrl_queue","RESET_SYSTEM")


  
  def auto( self, object_data ):
          object_data["reply"] = "AUTO"
          self.redis.set( "sprinkler_ctrl_mode","AUTO")
          self.redis.lpush( "sprinkler_ctrl_queue","AUTO")
   

  def clean_filter( self, object_data ):
     pass

  def open_master_valve( self, object_data ):
     pass


  def close_valve( self, object_data ):
     pass


  def set_auto_mode( self, object_data ):
     pass


  def queue_schedule( self, object_data ):
     object_data["reply"] = "QUEUE_SCHEDULE"
     self.redis_handle.lpush( "schedule_name_queue",object_data["schedule"] )
     self.redis_handle.lpush( "schedule_step_queue",1 )
     self.redis_handle.lpush( "schedule_time_queue",1)
     self.redis_handle.lpush( "sprinkler_ctrl_queue","QUEUE_SCHEDULE")

     

   
  def queue_schedule_step( self, object_data ):
     object_data["reply"] = "QUEUE_SCHDULE_STEP"
     self.redis_handle.lpush( "schedule_name_queue",object_data["schedule"] )
     self.redis_handle.lpush( "schedule_step_queue",object_data["step"] )
     self.redis_handle.lpush( "schedule_time_queue",1)
     self.redis_handle.lpush( "sprinkler_ctrl_queue","QUEUE_SCHEDULE_STEP")


  def queue_schedule_step_time( self, object_data ):
     object_data["reply"] = "QUEUE_SCHEDULE_STEP_TIME"
     self.redis_handle.lpush( "schedule_name_queue",object_data["schedule"] )
     self.redis_handle.lpush( "schedule_step_queue",object_data["step"]     )
     self.redis_handle.lpush( "schedule_time_queue",object_data["time"]     )
     self.redis_handle.lpush( "sprinkler_ctrl_queue","QUEUE_SCHEDULE_STEP_TIME")



  def turn_on_valve( self, object_data ):
     pass


  def turn_off_valve( self, object_data ): #same of
     pass
   
       
