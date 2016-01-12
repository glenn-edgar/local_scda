#
#  
#  File: passwords.py
#  This is an example file.  
#  Execute once during startup
#  Move out of distro directory
#


import redis
import json
redis                 = redis.StrictRedis( host = "127.0.0.1", port=6379, db = 1 )

redis.hset("gateway", "user_name", 'xxxxx' )
redis.hset("gateway", "password",  'xxxxx')
redis.hset("gateway", "vhost",     'xxxxx' )
redis.hset("gateway", "queue",     'xxxx')
redis.hset("gateway", "port",      5671  )
redis.hset("gateway", "server",    'xxxxx' )


redis.hset("alert", "user_name", 'xxxxx' )
redis.hset("alert", "password",  'xxxxx')
redis.hset("alert", "vhost",     'xxxxx' )
redis.hset("alert", "queue",     'xxxx')
redis.hset("alert", "port",      5671 )
redis.hset("alert", "server",    'xxxxx' )



redis.hset("web","crt_file", 'xxxxx')
redis.hset("web","key_file",'xxxx')
redis.hset("web","PORT",80 )
redis.hset("web","SECRET_KEY",'xxxxx')
redis.hset("web","DEBUG",True)
redis.hset("web","RealmDigestDB",'xxxxx')
redis.hset("web","users",json.dumps([{ "user":"xxxx","password":"xxxx" } ]))

