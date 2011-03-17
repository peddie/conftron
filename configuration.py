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
            cf.write("\n#include \"%(name)s_settings.h\"\n" % s)
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
                                   msgs,
                                   genconfig.config_folder,
                                   self.telemetryfile)

    def add_to_class_hash(self, hsh, cl):
        if hsh.has_key(cl.attrib['name']):
            hsh[cl.attrib['name']].append(cl)
        else:
            hsh[cl.attrib['name']] = [cl]
        return hsh

    def parse_classes(self, structs, structh, base, baseok):
        for cl in structs:
            if cl.tag == 'class':
                self.add_to_class_hash(structh, cl)
            elif cl.tag in baseok:
                cl.attrib['__base__'] = True
                base.append(cl)
            elif cl.tag == 'include':
                (structh, base) = self.parse_classes(ET.ElementTree().parse(genconfig.config_folder + cl.attrib['href']).getchildren(), structh, base, baseok)
        return (structh, base)

    def parse_types(self):
        ## Walk through the types, telemetry and settings definitions (allow arbitrary include depth)
        (structh, basestructs) = self.parse_classes(ET.ElementTree().parse(genconfig.config_folder + self.typesfile).getchildren(), 
                                     {}, [], ['struct', 'enum', 'message'])
        basestructs.reverse()
        (telemh, basetelem) = self.parse_classes(ET.ElementTree().parse(genconfig.config_folder + self.telemetryfile).getchildren(),
                                                 {}, [], [])
        (seth, baseset) = self.parse_classes(ET.ElementTree().parse(genconfig.config_folder + self.settingsfile).getchildren(),
                                             {}, [], [])

        self.classnames = set(structh.keys() + telemh.keys() + seth.keys())
        for clname in self.classnames:
            cscs = None
            if structh.has_key(clname):
                loc = []
                for cl in structh[clname]:
                    msgs = cl.getchildren()
                    [msgs.insert(0, b) for b in basestructs]
                    loc.append(structs.CStructClass(clname, cl, msgs))
                ## Uy veigh.  
                ready = reduce(lambda x, y: x.merge(y), loc)
                self.structs.append(ready)
                cscs = ready.structs
            if seth.has_key(clname):
                loc = []
                for cl in seth[clname]:
                    loc.append(settings.Settings(clname, 
                                                 cl.getchildren(), 
                                                 cscs, 
                                                 genconfig.config_folder, 
                                                 self.settingsfile))
                self.settings.append(reduce(lambda x, y: x.merge(y), loc))
                del seth[clname]
            if telemh.has_key(clname):
                loc = []
                for cl in telemh[clname]:
                    loc.append(self._create_telemetry_class(clname, cl, cscs))
                self.telemetry.append(reduce(lambda x, y: x.merge(y), loc))
                del telemh[clname]

