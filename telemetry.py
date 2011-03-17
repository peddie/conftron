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

class TelemetryMessage(baseio.CHeader, baseio.CCode, baseio.TagInheritance, baseio.OctaveCode):
    required_tags = ['flightrate', 'simrate']
    def __init__(self, hsh, parent):
        self.__dict__.update(hsh)
        self._inherit(parent)
        self._musthave(parent, telemetry_rates_error)
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

    def to_telemetry_emlc(self):
        filename = "octave/telemetry/%(classname)s_telemetry_%(type)s_%(varname)s" % self
        def out_fcn(cf):
            cf.write(emlc_telemetry_template % self)
        self.to_octave_code(filename, out_fcn)

class Telemetry(baseio.CHeader,
                baseio.LCMFile,
                baseio.CCode,
                baseio.TagInheritance,
                baseio.Searchable,
                baseio.IncludePasting):
    """This class represents a Telemetry class as taken from the XML
    config."""
    def __init__(self, classname, tel, class_structs, path, myfile):
        self.classname = classname
        self.path = path
        self.file = myfile
        self.__dict__.update(tel.attrib)
        self._filter_messages(tel.getchildren())
        self.sim_flag = genconfig.sim_flag
        self.timestep = genconfig.timestep
        self.class_struct_pointers = self._class_struct_pointers(class_structs)
        self.class_struct_includes = self._class_struct_includes(class_structs)

    def merge(self, other):
        ## The merge operation breaks a few things to do with internal
        ## consistency.  Basically, when we update the internal
        ## dictionary from the `other' instance, our local tags can be
        ## overwritten.  There's no good way around this within the
        ## current object hierarchy.  However, since the merge
        ## operation is not part of __init__(), the correct tags are
        ## propagated to the children of each instance _before_ they
        ## merge.  Basically, when you use the Configuration API,
        ## search for the properties of the actual object you want to
        ## deal with, and don't assume its parents will tell you what
        ## you want to know about it.

        for k, v in other.__dict__.iteritems():
            if not k in genconfig.reserved_tag_names:
                try:
                    # Is it a method?
                    getattr(getattr(self, k), "__call__")
                except AttributeError:
                    # Nope.
                    self.__dict__[k] = other.__dict__[k]
        self.messages.extend(other.messages)
        return self

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
        self.send_all = "\n".join(["  " + m.classname + "_" + m.varname + "_send(counter);" for m in self.messages])
        self.to_telemetry_h()
        self.to_telemetry_c()
        self.to_telemetry_emlc()
        self.telemetry_nops()

    def init_call(self):
        return lcm_init_call_template % self + "\n"

    def run_call(self):
        return lcm_run_call_template % self + "\n"

    def _filter_messages(self, msgs):
        flattened = self.insert_includes(msgs, ['message'])
        self.check_includes(flattened, ['message'])
        self.messages = [TelemetryMessage(dict(msg.attrib, **{'varname':msg.attrib['name']}), self) for msg in flattened]

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

    def to_telemetry_emlc(self):
        [m.to_telemetry_emlc() for m in self.messages]
