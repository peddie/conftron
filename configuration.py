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

from xml.etree import ElementTree as ET
import xml.parsers.expat as expat

import genconfig, baseio, telemetry, structs, settings

class Configuration(baseio.Searchable):
    def __init__(self, airframename=None):
        self.structs = []
        self.telemetry = []
        self.settings = []
        if airframename:
            self.settingsfile = airframename + "_settings.xml"
        else:
            self.settingsfile = "settings.xml"
        self.telemetryfile = "telemetry.xml"
        self.typesfile = "types.xml"

        self.parse_types()

    def search_structs(self, classname, searchname):
        scl = self._search(self.structs, classname)
        return scl.search(searchname)

    def search_telem(self, classname, searchname):
        scl = self._search(self.telemetry, classname)
        return scl.search(searchname)

    def search_settings(self, classname, searchname):
        scl = self._search(self.settings, classname)
        return scl.search(searchname)

    def make_lcm_handler(self, name, mtype, mclass):
        try: cls = self._search(self.structs, mclass).make_lcm_callback(mtype)
        except StopIteration: 
            print "Error!  No struct class by the name of %(class) in configuration!" % {'classname':mclass}
            return None

        def lcmcb(msg):
            return dict(cls(msg))
        
        return lcmcb

    def make_lcm_handler_from_telem(self, telemmsg):
        try: cls = (i for i in self.structs if i.name == telemmsg.classname).next().make_lcm_callback(telemmsg.type, telemmsg.varname + "_")
        except StopIteration: 
            print "Error!  No struct class by the name of %(class) in configuration!" % {'classname':telemmsg.classname}
            return None

        def lcmcb(msg):
            return dict(cls(msg))
        
        return lcmcb
        
    def codegen(self):
        clas = open(genconfig.classes_file, "w")
        [clas.write(cn + " ") for cn in self.classnames]
        clas.close()
        [c.codegen() for c in (self.structs + self.settings + self.telemetry)]
        lcm_auto = baseio.CHeader()
        lcm_auto.to_h(genconfig.lcm_settings_autogen, self.settings_header)
        lcm_auto.to_h(genconfig.lcm_telemetry_autogen, self.telemetry_header)

    ## Make lcm_settings_auto.h for inclusion into handwritten files
    def settings_header(self, cf):
        for s in self.settings:
            cf.write("#include \"%(name)s_settings.h\"\n" % s)
            s.settings_includes(cf)
        inits = "".join([s.init_call() for s in self.settings])
        checks = "".join([s.check_call() for s in self.settings])
        cf.write("\n\n" + settings.lcm_init_all_template % {"init_calls":inits})
        cf.write("\n\n" + settings.lcm_check_all_template % {"run_calls":checks})
        
    def telemetry_header(self, cf):
        for t in self.telemetry:
            cf.write("\n#include \"%(classname)s_telemetry.h\"\n" % t)
            t.telemetry_includes(cf)
        inits = "".join([t.init_call() for t in self.telemetry])
        runs = "".join([t.run_call() for t in self.telemetry])
        cf.write("\n\n" + telemetry.lcm_init_all_template % {"init_calls":inits})
        cf.write("\n\n" + telemetry.lcm_run_all_template % {"run_calls":runs})

    def _create_telemetry_class(self, clname, tel, msgs):
        return telemetry.Telemetry(clname, 
                                   tel,
                                   {'simrate':tel.attrib['sim'], 
                                    'flightrate':tel.attrib['flight']}, 
                                   msgs)

    def parse_types(self):
        ## Walk through the types, telemetry and settings definitions and
        ## create tuples of those that line up
        basestructs = []
        structh = {}
        telemh = {}
        seth = {}
        for cl in ET.ElementTree().parse(genconfig.config_folder + self.typesfile).getchildren():
            if cl.tag == 'class':
                structh[cl.attrib['name']] = cl
            elif cl.tag in ['struct', 'enum', 'message']:
                cl.attrib['__base__'] = True
                basestructs.append(cl)
        for cl in ET.ElementTree().parse(genconfig.config_folder + self.telemetryfile).getchildren():
            telemh[cl.attrib['name']] = cl
        for cl in ET.ElementTree().parse(genconfig.config_folder + self.settingsfile).getchildren():
            seth[cl.attrib['name']] = cl
        basestructs.reverse()

        self.classnames = set(structh.keys() + telemh.keys() + seth.keys())
        for clname in self.classnames:
            cscs = None
            csc = None
            tt = None
            ss = None
            if structh.has_key(clname):
                msgs = structh[clname].getchildren()
                [msgs.insert(0, b) for b in basestructs]
                csc = structs.CStructClass(clname, structh[clname], msgs)
                cscs = csc.structs
                self.structs.append(csc)
            if seth.has_key(clname):
                self.settings.append(settings.Settings(clname, seth[clname].getchildren(), cscs))
                del seth[clname]
            if telemh.has_key(clname):
                self.telemetry.append(self._create_telemetry_class(clname, telemh[clname], cscs))
                del telemh[clname]

