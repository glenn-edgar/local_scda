----
----
---- File: modbus_addr_lookup.lua
----
----
----
----
----
local temp
click_reg_address = {}

click_bit_address = {}

local integer_to_click = {}

integer_to_click["satellite_1"] = 
{
    "Y001","Y002","Y003","Y004", -- 1-4
    "Y101","Y102","Y103","Y104","Y105","Y106","Y107","Y108", -- 5 -12
    "Y201","Y202","Y203","Y204","Y205","Y206","Y207","Y208", -- 13 -20
    "Y301","Y302","Y303","Y304","Y305","Y306","Y307","Y308", -- 21 -28
    "Y401","Y402","Y403","Y404","Y405","Y406","Y407","Y408", -- 29 -36
    "Y501","Y502","Y503","Y504", -- 37 -40
    "Y601","Y602","Y603","Y604" -- 41 -44
}

integer_to_click["satellite_2"] = 
{
    "Y001","Y002","Y003","Y004", "Y005","Y006", -- 1-6
    "Y101","Y102","Y103","Y104","Y105","Y106","Y107","Y108", -- 7 -14
    "Y201","Y202","Y203","Y204","Y205","Y206","Y207","Y208" -- 15 -22
    
}


integer_to_click["satellite_3"] = 
{
    "Y001","Y002","Y003","Y004", "Y005","Y006", -- 1-6
    "Y101","Y102","Y103","Y104","Y105","Y106","Y107","Y108", -- 7 -14
    "Y201","Y202","Y203","Y204","Y205","Y206","Y207","Y208" -- 15 -22
    
}


for i = 1,500 do
 temp ="DF"..i

 click_reg_address[temp] = 0x7000+(i-1)*2
--  print("i",temp,click_reg_address[temp]))
end



for i = 1,1000 do
  temp = "DS"..i
  click_reg_address[ temp ] = i -1
end


for i = 1,256 do
  temp = "C"..i
  click_bit_address[ temp ] = 0x4000 + i -1
end

temp = { "01","02","03","04","05","06","07","08","09","10","12","13","14","15","16" }
for i,j in pairs(temp) do
     
   temp = "X0"..j
   click_bit_address[temp] = i-1
   temp = "X1"..j
   click_bit_address[temp] = 0x20 + i-1
   temp = "X2"..j
   click_bit_address[temp] = 0x40 + i-1
   temp = "X3"..j
   click_bit_address[temp] = 0x60 +i-1
   temp = "X4"..j
   click_bit_address[temp] = 0x80 + i-1
   temp = "X5"..j
   click_bit_address[temp] = 0xA0 + i-1
   temp = "X6"..j
   click_bit_address[temp] = 0xc0 + i-1
   temp = "X7"..j
   click_bit_address[temp] = 0xe0 + i-1
   temp = "X8"..j
   click_bit_address[temp] = 0x100 +i-1

   temp = "Y0"..j
   click_bit_address[temp] = 0x2000 +i-1
   temp = "Y1"..j
   click_bit_address[temp] = 0x2020 + i-1
   temp = "Y2"..j
   click_bit_address[temp] = 0x2040 + i-1
   temp = "Y3"..j
   click_bit_address[temp] = 0x2060 +i-1
   temp = "Y4"..j
   click_bit_address[temp] = 0x2080 + i-1
   temp = "Y5"..j
   click_bit_address[temp] = 0x20A0 + i-1
   temp = "Y6"..j
   click_bit_address[temp] = 0x20c0 + i-1
   temp = "Y7"..j
   click_bit_address[temp] = 0x20e0 + i-1
   temp = "Y8"..j
   click_bit_address[temp] = 0x2100 +i-1
end

for i = 1,999 do
  temp = "SC"..i
  click_bit_address[temp] = 0xf000 + i-1
end


function integer_to_click_address( satellite, input)
  local returnValue
  --print("!!!!!!!!!!!!! integer ",input)
  returnValue = integer_to_click[satellite][input]
  assert( returnValue ~= nil)
  --print("@@@@@@@@@@@@@@@ return ",returnValue)
  return returnValue
end
--ts.dump( click_bit_address )
--print( "X001", click_bit_address["X001"]) 
--print( "X80F", click_bit_address["X80F"]) 
--print( "Y001", click_bit_address["Y001"] )
--print( "Y80F", click_bit_address["Y80F"]) 
--os.exit()

