---
---
--- File: sprinkler_support.lua
---
--- note luaClock reads time to nano second resolution -- it is a c function

--- Modbus.lua has the form
--- these are the remote interfaces  position 4 which is nil is the handle
--- the fifth position is a slave that should be present on the interface or the physical interface is placed in position 1
--  modbus_tbl = { }
--  modbus_tbl[ "rtu_1" ] = { nil, ModbusRtuClient, 38400, nil, "satellite_1" } 
--  remote_devices = {}
--  remote_devices["satellite_1"] = { "rtu_1",100 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit            
--  remote_devices["satellite_2"] = { "rtu_1",125 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit  
--  remote_devices["satellite_3"] = { "rtu_1",170 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit       
--  remote_devices["satellite_3"] = { "rtu_1",150 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit


---
---
---




---
---
---
function load_initial_data()
  local tempString

  
  
  master_valve_list = js_files.import(sys_files.."/master_valve_setup.json")
  master_switch_list = js_files.import(sys_files.."/master_valve_switches.json")
  plc_inputs = js_files.import(sys_files.."/plc_inputs.json")
  global_flow_logging_sensors = js_files.import(sys_files.."/global_sensors.json")
  remote_io = js_files.import( sys_files.."/controller_pin_assignment.json")
  

end

---
---
---

function initialize_redis_queues( chainFlowHandle, chainObj, parameters, event )
  local flag

  flag, redis_connection  = redis.connect("127.1.1.1",0,1)
  
  assert(flag == true )
  return "DISABLE"
end


---
---
--- 
function enable_modbus_interface()
  dofile( sys_files.."/modbus.lua" )
  return "DISABLE"
end 



---
---
---
function compute_initial_time_ref()
 plc_time_base = {}
 for i,j in pairs( plc_inputs) do
   plc_time_base[i] = luaClock.readClock()  
 end
end



---
---
---
function initialize_comm_elements()
  set_up_redis_connection( redis_connection  )
  --print("start_up_remotes")
  start_up_remotes( modbus_tbl ) -- generates connection handle for entry in modbus_tbl
  --print("initial_time_ref")
  compute_initial_time_ref()


end


---
---
---
function disable_all_sprinklers( )
  local device
   local remote
   local table_data
  
  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = { 1 }
      modbus_write_bits_tbl( device[2],device[4], j[3], table_data )
      --log_event_data( schedule_name,event_actions.all_off, remote )
  end
  return "DISABLE"
end 


---
---
---

function measure_offset_current()
   local remote
   local device
  

  
   remote = "satellite_1"
   device = set_up_modbus_interface( remote )
   plc_current_offset =  modbus_read_float( device[2], device[4], "DF1" )
   coil_current_offset =  modbus_read_float( device[2], device[4], "DF2" )
  
end   



---
---
---
function  clear_global_counters ( chainFlowHandle, chainObj, parameters,event )
  local title 
  local remote 
  local flow_reg       
  local high_limit  
  local device
  local table_data
  local latch_bit 

  
 
  for i,j in pairs( plc_inputs) do
    remote         = j[1]
    latch_bit      = j[2]

    device = set_up_modbus_interface( remote )
    table_data = {1}
    modbus_write_bits_tbl(device[2],device[4],latch_bit, table_data )
    os.usleep(10000)
    table_data = {0}
    modbus_write_bits_tbl(device[2],device[4],latch_bit, table_data )
  end
 
  return "DISABLE"
end
---
---
---

function turn_off_master_valves()
     --if manual_flag == true then return end
     redis.data_store.set( redis_connection,"MASTER_VALVE_SETUP","OFF")
     for l,m in pairs( master_valve_list ) do
 
        remote = m[1]
        bits   = m[2]
        
        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 0}
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end 
      end
    

end

---
---
---
function modbus_write_wd_flag( chainFlowHandle,chainObj,parameters, event )
   local device
   local remote
   local table_data

  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = { 1 }
      modbus_write_bits_tbl( device[2],device[4], j[4], table_data )
  end
end 

---
---
--- tested
function initialize_io_server()
  initialize_redis_queues()
  --print("redis initialized")
  enable_modbus_interface()
  --print("modbus initialized")
  load_initial_data()
  --print("data loaded")
  initialize_comm_elements()
  --print("comm elements initializzed")
  disable_all_sprinklers()
  --print("sprinklers disabled")
  os.sleep(10)
  --print("made it past sleep")
  measure_offset_current()
  --print("measure offset current")
  clear_global_counters() 
  --print("clear global counters")
  turn_off_master_valves()
  --print("turn off master valves")
  modbus_write_wd_flag()
  --print("done")
end

---
---
--- Server Commands
--- note json_data is a dictionary
---
--- tested
function measure_current_server( json_data)
   local remote
   local device
   local plc_current
   local coil_current

  
   remote       = "satellite_1"
   device       = set_up_modbus_interface( remote )
   plc_current  =  modbus_read_float( device[2], device[4], "DF1" )
   plc_current  = plc_current - plc_current_offset
   
   coil_current =  modbus_read_float( device[2], device[4], "DF2" )
   coil_current = coil_current - coil_current_offset
   --print("coil_current",coil_current, coil_current_offset)
   --print("plc_current",plc_current,plc_current_offset)
   json_data["return_code"] = {}
   json_data["return_code"]["plc_current"] = plc_current
   json_data["return_code"]["coil_current"] = coil_current
   return json_data
end   

---
---
--- tested
function measure_flow_rate_server( json_data )

  local title 
  local remote 
  local flow_reg       

  local device
  local table_data
  local latch_bit 
  local flag
  local length
  local input_number
  local input_data
  local temp_time
  plc_input_registers = {}
  plc_raw_input_registers = {}
  for i,j in pairs( plc_inputs) do
    remote         = j[1]
    latch_bit      = j[2]
    input_register = j[3]
    input_number   = j[4]
    
    
    
    device = set_up_modbus_interface( remote )
    input_data = modbus_read_registers_tbl( device[2], device[4], input_register, input_number ) -- read flow sensor data
    table_data = {1}
    modbus_write_bits_tbl(device[2],device[4],latch_bit, table_data )  -- set toggle to clear interrupt devices
    os.usleep(10000)
    table_data = {0}
    modbus_write_bits_tbl(device[2],device[4],latch_bit, table_data ) -- clear for reset interrupt devices
    plc_input_registers[remote] = {}
    plc_raw_input_registers[remote] = {}
    temp_time = luaClock.readClock()
    for l = 1, input_number do
     plc_raw_input_registers[remote][l] = input_data[3+l]
     -- normalize flow rate to one minute time -- takes out random sampling jitter
     plc_input_registers[remote][l] = input_data[3+l]/(temp_time - plc_time_base[i] )*60.
    end
    plc_time_base[i] = temp_time
  end
 

  json_data["return_code"] = {}
  
  for i,j in pairs(global_flow_logging_sensors) do
    title          = j[1]
    remote         = j[2]
    input_number   = j[3]
   
    flow_value = plc_input_registers[remote][input_number]
    temp = {}
    temp["flow_value"] = flow_value
    temp["title"]      = title
    table.insert(json_data["return_code"], temp) 
  end 

  return json_data
end 

---
---
--- tested
function turn_on_master_valves_server( json_data )
     for l,m in pairs( master_valve_list ) do
 
        remote = m[1]
        bits   = m[2]
    
        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 1}
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end 
      end
      return json_data
end



---
---
---  
--- tested
function turn_off_master_valves_server( json_data )
     
     for l,m in pairs( master_valve_list ) do
       
        remote = m[1]
        bits   = m[2] 
        device = set_up_modbus_interface( remote )
      
        for i,j in pairs( bits ) do
           table_data = { 0}
        
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end 
      end
      
      return json_data
end


---
---
--- tested
function turn_on_cleaning_valves_server( json_data )

     
     for l,m in pairs( master_valve_list ) do
 
        remote = m[3]
        bits   = m[4]

        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 1}
           --print("######### master valve turn on type j ",remote, type(j),j)
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end 
      end
      return json_data    

end


----
----
----
--- tested
function turn_off_cleaning_valves_server(json_data)
    for l,m in pairs( master_valve_list ) do
 
        remote = m[3]
        bits   = m[4]

        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 0}
           --print("######### master valve turn off remote type j ",remote, type(j),j)
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end 
    end
    return json_data
end

---
---
--- tested
function modbus_read_wd_flag_server( json_data )
  local device
  local remote
  local table_data
  
  json_data["data"] = {}
  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = modbus_read_bits_tbl( device[2], device[4], j[4], 1 )
      json_data[j] = i
  end
  return json_data
end
  
---
---
---
---
--- tested
function modbus_write_wd_flag_server( json_data)
   local device
   local remote
   local table_data

  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = { 1 }
      -- j4 is the watch dog bit
      modbus_write_bits_tbl( device[2],device[4], j[4], table_data )
  end
  return json_data
end 


---
---
--- tested
function turn_on_io_server( json_data )
     local control
     local remote
     local device
     local table_data
     local duration
     local bits
     local plc_current
     local coil_current
     local returnValue
     local flag

     io_setup = json_data["io_setup"]
     --print("io_setup",io_setup) 
     io_setup = json.decode(io_setup)
     --ts.dump(io_setup)
     turn_on_master_valves_server()
   
     for l,m in pairs( io_setup ) do
 
        remote = m[1]
        bits   = m[2]
        --print("remote",remote)
	--ts.dump(bits)
        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 1}
           --print("######### remote type j ",remote, type(j),j)
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           input_data = modbus_read_bits_tbl( device[2], device[4], j, 1 )
        end 
      end
    
      os.sleep(5) -- wait 5 seconds
      ---
      --- Insure electrically that every thing is ok 
      --- 
      remote = "satellite_1"
      device = set_up_modbus_interface( remote )
      plc_current =  modbus_read_float( device[2], device[4], "DF1" )
      plc_current = plc_current - plc_current_offset
      coil_current =  modbus_read_float( device[2], device[4], "DF2" )
      coil_current = coil_current - coil_current_offset
      json_data["coil_current"] = coil_current
      json_data["plc_current"]  = plc_current
      json_data["active"] = 1
      if plc_current > 3.0 then
         json_data["active"] = 0
         turn_off_io( io_setup )
         disable_all_sprinklers()
         post_error("to_high_plc_current", remote, "plc_current" )
     end
    
     if coil_current > 24.0 then  -- cannot use # number as some sprinklers are currently doubled 
        json_data["active"] = 0               
        turn_off_io(io_setup)
        disable_all_sprinklers()
        post_error("to_high_coil_current", remote, "coil_current" )
     end
     return json_data
end


---
---
---
---  tested
function turn_off_io_server( json_data )
     local control
     local remote
     local device
     local table_data
     local duration
     local bits
    
     io_setup = json_data["io_setup"] 
     io_setup = json.decode(io_setup)
     turn_off_master_valves_server()

     for l,m in pairs( io_setup ) do
 
        remote = m[1]
        bits   = m[2]

        device = set_up_modbus_interface( remote )
        for i,j in pairs( bits ) do
           table_data = { 0}
           if type(j) == "number" then j = integer_to_click_address(remote,j) end
           modbus_write_bits_tbl(device[2],device[4],j, table_data )           
           
        end
          
     end
     return json_data
end

--- tested
--[[
function modbus_read_mode_switch( json_data )
  local device
  local remote
  local table_data
 
  
  for i, j in pairs( remote_devices) do
 
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = modbus_read_bits_tbl( device[2], device[4], j[6], 1 )
      if table_data[4] == 0 then
         equipment_alerts.remote_switch_note_in_run_mode( remote, 1 )
         store_alarm_queue( "read_mode_switch", "failure", "failure" )
          assert(false,"controller is not in run mode")
      end
      
  end
  return json_data
end
--]]

--- tested
function modbus_read_mode_switch( json_data )
  local device
  local remote
  local table_data
 
  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = modbus_read_bits_tbl( device[2], device[4], j[6], 1 )
      if table_data[4] == 0 then
         equipment_alerts.remote_switch_note_in_run_mode( remote, 1 )
         store_alarm_queue( "read_mode_switch", "failure", "failure" )
          assert(false,"controller is not in run mode")
      end
      
  end
  return json_data
end

--- tested
function modbus_read_wd_flag( json_data )
  local device
  local remote
  local table_data
  

  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = modbus_read_bits_tbl( device[2], device[4], j[4], 1 )
      if table_data[4] ~= 0 then
         equipment_alerts.remote_program_not_running( remote,1 )
         store_alarm_queue( "read_watch_dog_flag", "failure", "failure" )
	 assert(false,"controller is not running:  "..remote)
      end
  end
  return json_data
end

--- tested
function modbus_write_wd_flag( json_data )
   local device
   local remote
   local table_data

  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = { 1 }
      modbus_write_bits_tbl( device[2],device[4], j[4], table_data )
  end
  return json_data
end 

--- tested
function modbus_counters( json_data )
  construct_modbus_counters()
  return json_data
end

--- tested
function clean_filter_server( json_data )
   turn_off_cleaning_valves_server()
   turn_off_master_valves_server()
   os.sleep(5)
   turn_on_cleaning_valves_server()
   os.sleep(40)
   turn_on_master_valves_server()
   os.sleep(10)
   turn_off_master_valves_server()
   turn_off_cleaning_valves_server()
   return json_data
end


---
---
--- tested
function disable_all_sprinklers_server( json_data )
   local device
   local remote
   local table_data
  
  for i, j in pairs( remote_devices) do
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = { 1 }
      modbus_write_bits_tbl( device[2],device[4], j[3], table_data )
      
  end
  return json_data
end 

---
---
--- tested
function detect_switches_off(json_data)
  local returnValue
  local device
  local temp
  local input_data

  returnValue = false

  temp = master_switch_list.reset_switches
  for i,j in pairs(temp ) do
    device = set_up_modbus_interface( j[1] )
    input_data = modbus_read_bits_tbl( device[2], device[4], j[2], 1 ) 
   
   
    if input_data[4] ~= 0 then
     returnValue = true
    end
  end
 json_data["return_code"] = returnValue
 return json_data
end

---
---
--- tested

function check_switches_set( json_data )
  local returnValue
  local temp
  local device
  local input_register
  local input_number
  local device
  
  returnValue = false
  temp = master_switch_list.set_switches
 
  for i,j in pairs(temp ) do
    
    device = set_up_modbus_interface( j[1] )
   
    input_data = modbus_read_bits_tbl( device[2], device[4], j[2], 1 )

    if input_data[4] ~= 0 then
     returnValue = true
   end
  end
  json_data["return_code"] = returnValue
  return json_data
end

 

-- remote io
--{ "name":"satellite_1", "pins":44, "bits":["C201","C2","DS2"] }
-- tested
function clear_duration_counters( json_data   )

     local remote
     local reg
     local device
     local table_data
     local duration
     local bit


     for l,m in pairs( remote_io ) do
        remote = m.name
        bit    = m.bits[2]
        reg    = m.bits[3]
 
        table_data = { 0}
        device = set_up_modbus_interface( remote )
        modbus_write_bits_tbl(device[2],device[4],bit, table_data )
          
     end  
     return json_data  
end

-- io_setup  =  {{remote, {bit} }}
--- tested
function load_duration_counters( json_data )
     local control
     local remote
     local reg
     local device
     local table_data
     local duration
     local bit
     local bits
    

     time_duration = tonumber(json_data["time_duration"])

     for l,m in pairs(   remote_io ) do
        remote = m.name
        bit    = m.bits[2]
        reg    = m.bits[3]

        duration = (time_duration*60)+15 -- add 15 seconds to total duration
        device = set_up_modbus_interface( remote )

        table_data = { duration}
        modbus_write_registers_tbl(device[2],device[4], reg , table_data )
 
        table_data = { 0}
        modbus_write_bits_tbl(device[2],device[4],bit, table_data )
        table_data = { 1 }
        modbus_write_bits_tbl(device[2],device[4],bit, table_data )
          
     end    
     return json_data
end


function read_coil( json_data )
  local device
  local remote
  local table_data
  local return_value

  
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"] ) do
     remote   = j["remote"]
     register = j["register"]
     slave_id = j["slave_id"]
     device   = set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_read_coil_server( device[2], device[4], register )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end


function write_coil( json_data )
 local device
  local remote
  local table_data
  local return_value

  --print("write coil")
  --ts.dump(json_dump)
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"] ) do
     --print("j")
     --ts.dump(j)
     remote   = j["remote"]
     register = j["register"]
     value    = j["value"]
     slave_id = j["slave_id"]
     --print("json data",remote,register,value,slave_id)
     device   = set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_write_coil_register_server( device[2], device[4],register, value )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end

function read_register( json_data )
  local device
  local remote
  local table_data
  local return_value

  
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"]) do
     remote   = j["remote"]
     register = j["register"]
     slave_id = j["slave_id"]
     device   = special_set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_read_register_server( device[2], device[4], register  )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end

function write_register( json_data )
  local device
  local remote
  local table_data
  local return_value

  --print("write register") 
  --ts.dump(json_data) 
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"] ) do
     --print("j")
     --ts.dump(j)

     remote   = j["remote"]
     register = j["register"]
     value    = j["value"]
     slave_id = j["slave_id"]
     device   = special_set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_write_register_server( device[2], device[4], register, value )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end





function read_float( json_data )
  local device
  local remote
  local table_data
  local return_value

  
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"] ) do
     remote   = j["remote"]
     register = j["register"]
     slave_id = j["slave_id"]
     device   = special_set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_read_float_server( device[2], device[4], register )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end


function write_float( json_data )
  local device
  local remote
  local table_data
  local return_value
  local slave_id

  
  json_data["return_code"] = {}
  for i, j in pairs( json_data["io_list"] ) do
     remote   = j["remote"]
     register = j["register"]
     value    = j["value"]
     slave_id = j["slave_id"]
     device   = special_set_up_modbus_interface( remote ,slave_id )
     results  =  modbus_write_float_server( device[2], device[4], register, value )
     table.insert( json_data["return_code"], results)
  end
  return json_data
end


    
sys_files = "/media/mmc1/system_data_files"


server_commands = {}
server_commands["detect_switches_off"]         = detect_switches_off               --- tested
server_commands["check_switches_set"]          = check_switches_set                --  tested
server_commands["measure_current"]             = measure_current_server            --- tested
server_commands["measure_flow_rate"]           = measure_flow_rate_server          --  tested
server_commands["disable_all_sprinklers"]      = disable_all_sprinklers_server     --- tested
server_commands["turn_on_master_valves"]       = turn_on_master_valves_server      --- tested
server_commands["turn_off_master_valves"]      = turn_off_master_valves_server     --- tested
server_commands["turn_on_cleaning_valves"]     = turn_on_cleaning_valves_server    --- tested
server_commands["turn_off_cleaning_valves"]    = turn_off_cleaning_valves_server   --- tested  
server_commands["turn_off_io"]                 = turn_off_io_server                --- tested
server_commands["modbus_read_wd_flag"]         = modbus_read_wd_flag_server        --- tested
server_commands["modbus_write_wd_flag"]        = modbus_write_wd_flag_server       --- tested
server_commands["turn_on_io"]                  = turn_on_io_server                 --- tested
server_commands["modbus_read_mode"]            = modbus_read_mode_switch           --- tested
server_commands["modbus_read_mode_switch"]     = modbus_read_mode_switch           --- tested
server_commands["modbus_read_wd_flag"]         = modbus_read_wd_flag               --- tested
server_commands["modbus_write_wd_flag"]        = modbus_write_wd_flag              --- tested
server_commands["construct_modbus_counters"]   = modbus_counters                   --- tested
server_commands["clean_filter"]                = clean_filter_server               --- tested
server_commands["clear_duration_counters"]     = clear_duration_counters           --- tested
server_commands["load_duration_counters"]      = load_duration_counters            --- tested
server_commands["read_coil"]                   = read_coil
server_commands["write_coil"]                  = write_coil
server_commands["read_register"]               = read_register
server_commands["write_register"]              = write_register
server_commands["read_float"]                  = read_float
server_commands["write_float"]                 = write_float



--- tested
function io_server()
  local flag,temp
  flag = true
  print("empting preexisting queue")
  while flag do
     temp, length = redis.job_queue.length( redis_connection,"io_ctrl_queue")
     if length > 0 then
       redis.job_queue.pop( redis_connection,"io_ctrl_queue")
     else
       flag = false
     end
  end
  --print("queue has been emptied")
  
  while true do
      flag, length = redis.job_queue.length( redis_connection, "io_ctrl_queue" )
      if length ~= 0 then
         flag, temp = redis.job_queue.pop( redis_connection,"io_ctrl_queue")
         temp = base64.decode(temp)
         --print("io server data ",temp)
         temp_object = json.decode(temp)
         if server_commands[ temp_object["command"] ] ~= nil then
             --print("dumping temp object")
             --ts.dump(temp_object)
             temp_object = server_commands[ temp_object["command"]]( temp_object )
             if temp_object["return_queue"] ~= nil then
               temp = json.encode( temp_object )
               --print("temp",temp)
               temp = base64.encode( temp )
               redis.job_queue.push( redis_connection, temp_object["return_queue"], temp )
             end -- if return queue is nil
         else -- if valid command
           print("not a valid command ",temp)
         end
     else
       os.usleep(10000) -- .01 secondes
     end -- if length
      
  end -- end while
 
end -- end io_server


---
---
--- start of progarm
---
---
--print("made it here")
initialize_io_server()
print("ready to serve commands")
io_server()
