import lcm, sys

sys.path.append("../")
import ap

lc = lcm.LCM()

def confirm(channel, data):
    msg = ap.xyz_t.decode(data)
    print """Received confirmation message on channel %(channel)s, 
   x = %(x)s; y = %(y)s; z = %(z)s
""" % {"channel":str(channel), "x":str(msg.x), "y":str(msg.y), "z":str(msg.z)}

subscription = lc.subscribe("ap_xyz_t_foobar_ack", confirm)

msg = ap.xyz_t()
msg.x = 1
msg.y = 1
msg.z = 1

lc.publish("ap_xyz_t_foobar_set", msg.encode())

lc.handle()

lc.unsubscribe(subscription)




