import lcm, sys

sys.path.append("../")
import ap

lc = lcm.LCM()

msg = ap.xyz_t()
msg.x = 1
msg.y = 1
msg.z = 1

lc.publish("ap_xyz_t", msg.encode())
