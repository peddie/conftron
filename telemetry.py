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

import genconfig, baseio
from telemetry_templates import *

class TelemetryMessage(baseio.CHeader, baseio.CCode, baseio.ImADictionary):
    def __init__(self, hsh):
        self.__dict__.update(hsh)
        self.sim_flag = genconfig.sim_flag
        self.timestep = genconfig.timestep
        self.lcm_folder = genconfig.lcm_folder
        if not self.has_key('channel'):
            self.channel = "%(classname)s_%(type)s_%(varname)s" % self

    def to_telemetry_function(self):
        """This emits a small function that relies on a variable being
        captured by scoping rules to send the struct as telemetry."""

        filename = genconfig.telemetry_folder + "/%(classname)s_%(type)s_%(varname)s" % self
        def th(cf):
            cf.write("#include <%(classname)s_telemetry.h>\n" % self)
            cf.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n");
            if self.has_key('channel'):
                cf.write(lcm_telemetry_custom_chan_template % self)
            else:
                cf.write(lcm_telemetry_template % self)
            cf.write("#ifdef __cplusplus\n}\n#endif\n\n");
        self.to_h(filename, th)

    def to_telemetry_prototype(self, cf):
        """This emits a function prototype for the telemetry capture
        function created above."""
        
        proto = """\
void %(classname)s_%(varname)s_send(int counter); \n""" % self
        cf.write(proto)

    def to_telemetry_nop(self):
        filename = genconfig.stubs_folder + "/%(classname)s_%(type)s_%(varname)s_telem_stub" % self
        def stub_f(cf):
            cf.write(lcm_telemetry_nop_template % self)
        self.to_c_no_h(filename, stub_f)



class Telemetry(baseio.CHeader, baseio.LCMFile, baseio.CCode, baseio.ImADictionary, baseio.Searchable):
    """This class represents a Telemetry class as taken from the XML
    config."""
    def __init__(self, classname, msgs, ratedict, class_structs):
        self.classname = classname
        self.__dict__.update(ratedict)
        self.messages = self._filter_messages(msgs)
        self.sim_flag = genconfig.sim_flag
        self.timestep = genconfig.timestep
        self.send_all = "\n".join(["  " + m.classname + "_" + m.varname + "_send(counter);" for m in self.messages])
        self.class_struct_pointers = self._class_struct_pointers(class_structs)
        self.class_struct_includes = self._class_struct_includes(class_structs)

    def search(self, searchname):
        return self._search(self.messages, searchname)

    def get_lcm_channel(self, name):
        try: ff = self.search(name)
        except StopIteration: 
            print "Error!  No message by the name of %(name) in class %(classname)!" % {'name':name, 'classname':self.classname}
            return None
        else:
            return ff.channel

    def codegen(self):
        self.to_telemetry_h()
        self.to_telemetry_c()
        self.telemetry_nops()

    def init_call(self):
        return lcm_init_call_template % self + "\n"

    def run_call(self):
        return lcm_run_call_template % self + "\n"

    def _filter_messages(self, msgs):
        outstructs = []
        for msg in msgs:
            if msg.tag == 'message':
                if not msg.attrib.has_key('flight'):
                    msg.attrib['flight'] = self.flightrate
                if not msg.attrib.has_key('sim'):
                    msg.attrib['sim'] = self.simrate
                outstructs.append(TelemetryMessage(dict(msg.attrib, **{'classname':self.classname,
                                                                       'simrate':msg.attrib['sim'], 
                                                                       'flightrate':msg.attrib['flight'],
                                                                       'varname':msg.attrib['name']})))
            else:
                print baseio.parse_type_error % {"msg_tag":msg.tag, "filename":"telemetry"}
        return outstructs

    def _class_struct_pointers(self, structs):
        out = []
        formatstr = "  %(classname)s_%(type)s_subscription_t *%(type)s_sub;" 
        if (structs):
            out = [formatstr % s for s in structs]
        else:
            ## If this is an orphaned telemetry module, we'll only add
            ## pointers for structs we know about.
            out = [formatstr % m for m in self.messages]
        return "\n".join(out)

    def _class_struct_includes(self, structs):
        out = []
        formatstr = "#include \"%(lcm_folder)s/%(classname)s_%(type)s.h\""
        if (structs):
            out = [formatstr % s for s in structs]
        else:
            ## Orphaned telemetry module; include only types we know
            ## about
            out = [formatstr % m for m in self.messages]
        return "\n".join(out)

    def telemetry_run_function(self, cf):
        """Generate a top-level function for sending all appropriate
        telemetry messages (simply calling all the sub-functions for
        telemtry) """
        cf.write(lcm_run_template % self)

    def telemetry_includes(self, cf):
        cf.write(self.class_struct_includes)
        
    def telemetry_nops(self):
        for m in self.messages:
            m.to_telemetry_nop()

    def telemetry_lcm_struct(self, cf):
        cf.write(lcm_struct_template % self)

    def telemetry_prototypes(self, cf):
        """Generate a series of prototypes for the individual
        telemetry message sending functions"""
        for m in self.messages:
            m.to_telemetry_prototype(cf)

    def telemetry_functions(self):
        for m in self.messages:
            m.to_telemetry_function()

    def to_telemetry_c(self):
        def telem_f(cf):
            cf.write("#include \"lcm_interface.h\"\n")
            cf.write("#include \"%(classname)s_types.h\"\n\n" % self)
            cf.write("%(classname)s_lcm_t %(classname)s_lcm;\n\n" % self)
            self.telemetry_prototypes(cf)
            cf.write(lcm_init_template % self)
            self.telemetry_run_function(cf)

        self.to_c(self.classname+"_telemetry", telem_f)

    def to_telemetry_h(self):
        self.telemetry_functions()
        def telem_f(cf):
            self.telemetry_includes(cf)
            self.telemetry_lcm_struct(cf)
            protos = "\n".join([lcm_init_prototype_template % self, 
                                lcm_run_prototype_template % self])
            cf.write(self.cpp_wrap(protos))
            cf.write(lcm_macros_template % self)
        self.to_h(self.classname + "_telemetry", telem_f)


