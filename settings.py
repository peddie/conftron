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
from settings_templates import *

class LCMSettingField(baseio.TagInheritance):
    required_tags = ['default', 'step', 'min', 'max']
    def __init__(self, hsh, parent):
        self.__dict__.update(hsh)
        self._inherit(parent)
        if self.has_key('absmax'):
            self.min = -float(self.absmax)
            self.max = float(self.absmax)
        self.parent = parent
        self.parentname = parent.name
        self._musthave(parent, parse_settings_noval)
        self.classname = parent.classname
        parent.die += self._filter()

    def field_setting(self):
        return lcm_settings_field_template_mm % self

    def _filter(self):
        die = 0
        die += self._are_defaults_sane()
        return die

    def _are_defaults_sane(self):
        ## Default values outside the range given by the bounds
        ## don't make sense either.
        die = 0
        if (float(self['min']) > float(self['default'])
            or float(self['max']) < float(self['default'])):
            print parse_settings_badval % {"sp":'default', 
                                           "f":self['name'], 
                                           "s":self.parent['name'], 
                                           "max":self['max'], 
                                           "min":self['min'], 
                                           "val":self['default']} 
            die += 1
        if float(self['step']) > (float(self['max']) - float(self['min'])):
            print parse_settings_badval % {"sp":'default', 
                                           "f":self['name'], 
                                           "s":self.parent['name'], 
                                           "max":self['max'], 
                                           "min":self['min'], 
                                           "val":self['step']} 
            die += 1
        return die

class LCMSetting(baseio.CHeader, baseio.LCMFile, baseio.CCode, baseio.TagInheritance, baseio.IncludePasting):
    def __init__(self, s, parent):
        self.__dict__.update(s.attrib)
        self.classname = parent.name
        self._inherit(parent)
        self.lcm_folder = genconfig.lcm_folder
        self.die = 0
        self.make_fields(s.getchildren())
        self.field_settings = "\n".join([f.field_setting() for f in self.fields])

    def make_fields(self, fields):
        flattened = self.insert_includes(fields, ['member'])
        self.check_includes(flattened, ['member'])
        self.fields = [LCMSettingField(dict(f.attrib, **{'varname':self.varname}), self) for f in flattened]

    def to_settings_file(self):
        basename = "%(classname)s_%(type)s_%(varname)s" % self
        filename = genconfig.settings_folder + "/" + basename
        def sf(cf):
            cf.write("#include <lcm/lcm.h>\n" % self)
            cf.write("#include <math.h>\n" % self)
            cf.write("#include <%(classname)s_settings.h>\n" % self)
            if self.has_key('channel'):
                cf.write(lcm_settings_init_custom_chan_template % self)
            else:
                cf.write(lcm_settings_init_template % self)
            cf.write(lcm_settings_func_template % self)
        self.to_h(filename, sf)

    def to_settings_nop(self):
        filename = genconfig.stubs_folder + "/%(classname)s_%(type)s_%(varname)s_setting_stub" % self
        def stub_f(cf):
            cf.write("#include <lcm_settings_auto.h>\n\n")
            cf.write(lcm_settings_init_nop_template % self)
            cf.write(lcm_settings_set_nop_template % self)
        self.to_c_no_h(filename, stub_f)

    def to_settings_prototype(self, cf):
        cf.write(lcm_settings_prototype % self)

class Settings(baseio.CHeader, 
               baseio.LCMFile, 
               baseio.CCode, 
               baseio.TagInheritance, 
               baseio.Searchable,
               baseio.IncludePasting):
    def __init__(self, name, children, class_structs, path, filename):
        self.name = name
        self.path = path
        self.file = filename
        self.classname = name
        self._filter_settings(children)
        self.class_struct_includes = self._class_struct_includes(class_structs)

    def merge(self, other):
        for k, v in other.__dict__.iteritems():
            if not k in genconfig.reserved_tag_names:
                try:
                    # Is it a method?
                    getattr(getattr(self, k), "__call__")
                except AttributeError:
                    # Nope.
                    self.__dict__[k] = other.__dict__[k]
        self.settings.extend(other.settings)
        return self

    def search(self, searchname):
        return self._search(self.settings, searchname)

    def codegen(self):
        self.init_calls = "\n".join([lcm_settings_init_call_template % s for s in self.settings])
        self.null_calls = "\n".join([lcm_settings_init_null_template % s for s in self.settings])
        self.to_settings_h()
        self.settings_nops()

    def init_call(self):
        return "  %(classname)s_settings_init(provider); \\\n" % self

    def check_call(self):
        return "  %(classname)s_settings_check(); \\\n" % self

    def _filter_settings(self, structs):
        die = 0
        flattened = self.insert_includes(structs, ['struct'])
        self.check_includes(flattened, ['struct'])
        outstructs = [LCMSetting(s, self) for s in flattened]
        die = sum([s.die for s in outstructs])
        if die:
            print "Lots of settings errors detected; cannot continue code generation."
            sys.exit(1)
        self.settings = outstructs

    def settings_functions(self):
        for s in self.settings:
            s.to_settings_file()

    def settings_prototypes(self, cf):
        cf.write("/* Prototypes for all the functions defined in settings/ folder */\n")
        for s in self.settings:
            cf.write(lcm_settings_prototype % s)
            cf.write(lcm_settings_init_prototype % s)

    def settings_nops(self):
        for s in self.settings:
            s.to_settings_nop()

    def _class_struct_includes(self, structs):
        out = []
        formatstr = "#include \"%(lcm_folder)s/%(classname)s_%(type)s.h\""
        if (structs):
            out = [formatstr % s for s in structs]
        else:
            ## Orphaned settings module; include only types we know
            ## about
            out = [formatstr % s for s in self.settings]
        return "\n".join(out)

    def settings_includes(self, cf):
        cf.write(self.class_struct_includes)

    def to_settings_periodic(self):
        pass

    def to_settings_c(self):
        pass

    def to_settings_h(self):
        self.settings_functions()
        def settings_f(cf):
            cf.write("#include \"%(classname)s_types.h\"\n\n" % self)
            cf.write("#include \"%(classname)s_telemetry.h\"\n\n" % self)
            cf.write("#ifdef __cplusplus\n")
            cf.write("extern \"C\"{\n")
            cf.write("#endif\n\n")
            self.settings_prototypes(cf)
            cf.write("\n#ifdef __cplusplus\n")
            cf.write("}\n")
            cf.write("#endif\n")
            # Make initialization macro
            cf.write(lcm_settings_init_class_template % self)
            cf.write(lcm_check_call_template % self);
        self.to_h(self.name + "_settings", settings_f)

