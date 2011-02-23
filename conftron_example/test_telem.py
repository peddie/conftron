import lcm, sys

sys.path.append("../")
import ap

lc = lcm.LCM()

def telem(channel, data):
    msg = ap.xyz_t.decode(data)
    print """Received telemetry message on channel %(channel)s, 
   x = %(x)s; y = %(y)s; z = %(z)s
""" % {"channel":str(channel), "x":str(msg.x), "y":str(msg.y), "z":str(msg.z)}

subscription = lc.subscribe("ap_xyz_t_foobar", telem)

try:
    while True:
        lc.handle()
except KeyboardInterrupt:
    pass

lc.unsubscribe(subscription)
