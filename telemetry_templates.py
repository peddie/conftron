## This file is part of conftron.  
## 
## Copyright (C) 2011 Matt Peddie <peddie@jobyenergy.com>
## 
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

## Run telemetry functions
lcm_run_prototype_template = "void %(classname)s_telemetry_send(void);"

lcm_run_call_template = "  %(classname)s_telemetry_send();  \\"

lcm_run_all_template = """
#define telemetry_send() { \\
%(run_calls)s }
"""

lcm_telemetry_template = """
void 
%(classname)s_%(varname)s_send(int counter)
{
#ifdef %(sim_flag)s
  if ((counter %% ((int) (1.0/(%(timestep)s * %(simrate)s)))) == 0) 
#else
  if ((counter %% ((int) (1.0/(%(timestep)s * %(flightrate)s)))) == 0) 
#endif // %(sim_flag)s
    %(classname)s_lcm_send_chan(&%(varname)s, %(type)s, "%(classname)s_%(type)s_%(varname)s");
}
"""

lcm_telemetry_custom_chan_template = """
void 
%(classname)s_%(varname)s_send(int counter)
{
#ifdef %(sim_flag)s
  if ((counter %% ((int) (1.0/(%(timestep)s * %(simrate)s)))) == 0) 
#else
  if ((counter %% ((int) (1.0/(%(timestep)s * %(flightrate)s)))) == 0) 
#endif // %(sim_flag)s
    %(classname)s_lcm_send_chan(&%(varname)s, %(type)s, "%(channel)s");
}
"""

lcm_telemetry_nop_template = """
void 
%(classname)s_%(varname)s_send(int counter __attribute__((unused)))
{
  return;
}
"""

lcm_run_template = """\
void
%(classname)s_telemetry_send(void)
{
  static int counter = 0;

%(send_all)s

  if (counter >= (int) (1.0/(%(timestep)s))) counter = 0;
  else counter++;
}
"""

## Init all lcm stuff
lcm_init_call_template = "  %(classname)s_lcm_init(provider);  \\"

lcm_init_all_template = """
#define lcm_init(provider) { \\
%(init_calls)s } 
"""

lcm_init_prototype_template = "void %(classname)s_lcm_init(const char *provider);\n"

lcm_init_template = """
void
%(classname)s_lcm_init(const char *provider)
{
  if (%(classname)s_lcm.lcm == NULL)
    lcm_initialize(provider, &%(classname)s_lcm.lcm, &%(classname)s_lcm.fd);
}
"""


## Form structs per-class for telemetry
lcm_struct_template = """
typedef struct %(classname)s_lcm_t {
  lcm_t *lcm;
%(class_struct_pointers)s
  int fd;
} %(classname)s_lcm_t;

extern %(classname)s_lcm_t %(classname)s_lcm;
"""

## Simple lcm i/o interface for manually sending and manipulating LCM
## messages
lcm_macros_template = """

#define %(classname)s_lcm_send_chan(msg, msgtype, chan) {                \\
    %(classname)s_ ## msgtype ## _publish(%(classname)s_lcm.lcm, chan, (const %(classname)s_ ## msgtype *) msg); \\
  }

#define %(classname)s_lcm_send(msg, msgtype) {                                \\
  %(classname)s_lcm_send_chan(msg, msgtype, "%(classname)s_" #msgtype);                 \\
  }

/* type      the type of the message (e.g. est2User_t) 
 * handler   a function of type lcm_msg_handler_t (e.g. &update_e2u)
 * data      pointer to be passed to handler whenever it's called
 * channel   optional channel name 
 */

#define %(classname)s_lcm_subscribe_chan(type, handler, data, channel) {                        \\
  %(classname)s_lcm.type ## _sub =                                                          \\
    %(classname)s_ ## type ## _subscribe(%(classname)s_lcm.lcm, channel, handler, data);       \\
  }

/* assume channel the same as the type */

#define %(classname)s_lcm_subscribe(type, handler, data) {                                 \\
  %(classname)s_lcm_subscribe_chan(type, handler, data, "%(classname)s_" # type);                      \\
  }


/* Generate a handler that does nothing but copy the message to the
 * given pointer. */

#define %(classname)s_lcm_copy_handler(type)                                               \\
  static void                                                                   \\
  type ## _handler(const lcm_recv_buf_t *rbuf __attribute__((unused)),  \\
                   const char *channel __attribute__((unused)),                 \\
                   const %(classname)s_ ## type *msg,                                      \\
                   void *user)                                         \\
  {                                                                             \\
    if (user)                                                           \\
      memcpy((type *)user, msg, sizeof(type));                          \\
  }                                                                             

/* Subscribe to the handler generated above for the same type. */

#define %(classname)s_lcm_subscribe_cp(type, data) {                                       \\
    %(classname)s_lcm_subscribe(type, & type ## _handler, data);          \\
  }

#define %(classname)s_lcm_subscribe_chan_cp(type, data, chan) {                \\
    %(classname)s_lcm_subscribe_chan(type, & type ## _handler, data, chan);         \\
  }


#define %(classname)s_lcm_unsubscribe(type) {                                              \\
  %(classname)s ## type ## _unsubscribe(%(classname)s_lcm.lcm, %(classname)s_lcm. ## type ## _sub);      \\
  }

/* In case you want to change handlers, channel or user data.  Note
 * that you've gotta pass all the arguments again (for now). */

#define %(classname)s_lcm_resubscribe_chan(type, handler, data, channel) {         \\
  %(classname)s_lcm_unsubscribe(type);                                             \\
  %(classname)s_lcm_subscribe_chan(type, handler, data, channel);                  \\
  }

#define %(classname)s_lcm_resubscribe(type, handler, data) {                       \\
  %(classname)s_lcm_unsubscribe(type);                                             \\
  %(classname)s_lcm_subscribe(type, handler, data);                                \\
  }

"""

telemetry_rates_error = """
Error: Telemetry generation couldn't derive a value for the required
parameter `%(tag)s' for message `%(varname)s'.  Make sure you provide
this parameter in the telemetry configuration file, or I won't know
when to send your messages.
"""
