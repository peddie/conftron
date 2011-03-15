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

lcm_primitives = ["double", "float", "int32_t", "int16_t", "int8_t"]

class StructField(baseio.ImADictionary):
    def __init__(self, attrib):
        self.__dict__.update(attrib)
        if self.has_key('array'):
            self.sizes = self.array.rsplit(",")

    def to_cstring(self):
        # handle pointers
        ptr = None
        if self.has_key('ptr'):
            ptr = self.ptr.count('*')
            if ptr == 0 and self.has_key('ptr'):
                ptr = int(self.ptr)
        # field name
        fstr = self.type + " " + self.name
        if ptr: fstr += '[1]'*ptr 
        # handle arrays
        if self.has_key('array'):
            for s in self.sizes:
                fstr += "[" + s + "]"
        fstr += ";"
        # comments and units (appended to comment)
        if self.has_key('comment') or self.has_key('unit'):
            fstr += "\t\t" + "// "
        if self.has_key('unit'):
            fstr += "(" + self.unit + ") -- "
        if self.has_key('comment'):
            fstr += self.comment
        fstr += "\n"
        return fstr

    def to_lcm_callback(self, prefix=""):
        if self.has_key('array'):
            return self.to_lcm_callback_array(prefix)
        else:
            return self.to_lcm_callback_single(prefix)

    def to_lcm_callback_single(self, prefix):
        if self.type in lcm_primitives:
            def return_primitive(msg):
                return [(prefix + self.name, msg)]
            return return_primitive
        else:
            nextfn = self.cl.make_lcm_callback(self.type, prefix + self.name + "_")
            def return_another_struct(msg):
                return nextfn(msg)
            return return_another_struct
                
    def to_lcm_callback_array(self, prefix):
        if self.type in lcm_primitives:
            def return_array(msg):
                return [(prefix + self.name + "_" + str(n), msg[n]) for n in xrange(int(self.sizes[0]))]
            return return_array
        else:
            nextfns = []
            for n in xrange(int(self.sizes[0])):
                nextfns.append((n, self.cl.make_lcm_callback(self.type, prefix + self.name + "_" + str(n) + "_")))
            def return_array(msg):
                return [f(msg[n]) for n, f in nextfns]
            return return_array
                

class LCMStruct(baseio.ImADictionary):
    """This is the native format for structs we need to use.  You can
    convert to and from XML, C, LCM and Python."""
    def __init__(self, msg, classname):
        self.__dict__.update(msg.attrib)
        self.members = [StructField(dict(m.attrib, **{'cl':self.cl})) for m in msg.getchildren()]
        self.classname = classname
        self.type = self.name
        self.lcm_folder = genconfig.lcm_folder

    def to_lcm_callback(self, prefix=""):
        member_callbacks = [(m, m.to_lcm_callback(prefix)) for m in self.members]
        def return_data(msg):
            fields = []
            [fields.extend(mc(getattr(msg, m.name))) for m, mc in member_callbacks]
            return fields
        return return_data

    def to_c(self):
        """This emits additional C code (struct definitions) for all
        the messages described, plus the #define-d enum contents since
        LCM doesn't implement enum types."""
        outstr = ""
        if self.has_key('__base__'):
            outstr += "#ifndef " + self.name.upper() + "\n"
            outstr += "#define " + self.name.upper() + "\n"
        outstr += "typedef struct " + self.name + " {\n" # self.classname + "_" + 
        if self.has_key('comment'):
            outstr += "/* " + self.comment + " */\n"
        for m in self.members: 
            outstr += "  " + m.to_cstring()
        outstr += "} " + self.name + ";\n" # + self.classname + "_" 
        if self.has_key('__base__'):
            outstr += "#endif // " + self.name.upper() + "\n"
        return outstr
        
    def to_lcm(self):
        """This emits the LCM configuration file based on the structs
        described in XML."""
        outstr = "struct " + self.name + " {\n" # self.classname + "_" + 
        if self.has_key('comment'):
            outstr += "/* " + self.comment + " */\n"
        for m in self.members: 
            outstr += "  " + m.to_cstring()
        outstr += "}\n"
        return outstr

    def to_include(self):
        pass
        
    def to_python(self):
        """This emits Python classes (mainly just with attributes)
        based on the messages described in XML, along with hashes for
        the enums since LCM doesn't implement enum types."""
        print "Compiling XML directly to python classes is not implemented. --MP"

class LCMEnum(baseio.ImADictionary):
    def __init__(self, enum, clname):
        self.__dict__.update(enum.attrib)
        self.fields = [f.strip() for f in self.fields.rsplit(',')]
        self.classname = clname
        self.type = self.name
        self.lcm_folder = genconfig.lcm_folder

    def to_lcm_callback(self, prefix=""):
        def cb(msg):
            return [(prefix + self.name, msg.val)]
        return cb

    def get_fields_with_indices(self):
        return dict(zip(self.fields, range(len(self.fields))))
    
    def get_indices_with_fields(self):
        return dict(zip(range(len(self.fields)), self.fields))

    def to_c(self):
        estr = ""
        if self.has_key('comment'):
            estr += "/* " + self.comment + " */\n"
        if self.has_key('__base__'):
            estr += "#ifndef " + self.name.upper() + "\n"
            estr += "#define " + self.name.upper() + "\n"
        estr += "typedef " 
        estr += "enum {\n"
        for (k,f) in enumerate(self.fields):
            estr += "  " + f + " = "+str(k)+",\n"
        estr += "} "
        if self.has_key('typedef'):
            estr += self.typedef
        else:
            estr += self.name
        estr += ";\n"
        if self.has_key('__base__'):
            estr += "#endif // " + self.name.upper() + "\n"
        return estr

    def to_c_defines(self):
        """We use #defines to implement a hacky enum.  Simply typedef
        int to command_t and use the preprocessor values.  The
        autogenerated code takes care of the rest.  This means that
        you still have to extract the "val" field or just typecast
        it."""

        estr = ""
        if self.has_key('comment'):
            estr += "/* " + self.comment + " */\n"
        estr += "typedef int " + self.name + ";\n"
        defenum = zip(self.fields, range(len(self.fields)-1))
        for f, n in defenum:
            estr += "#define " + f + " " + str(n) + "\n"
        return estr

    def to_lcm(self):
        estr = "struct " + self.name + " {\n  int32_t val;\n}\n"
        return estr

    def to_include(self):
        pass

    def to_python(self):
        print "Compiling XML directly to python classes is not implemented. --MP"

class CStructClass(baseio.CHeader, baseio.LCMFile, baseio.CCode, baseio.Searchable):
    def __init__(self, name, structs):
        self.name = name
        self.structs = self._filter_structs(structs)

    def search(self, searchname):
        return self._search(self.structs, searchname)

    def make_lcm_callback(self, name, prefix=""):
        try: 
            ff = self.search(name)
        except StopIteration: 
            print "Error!  No struct by the name of %(name) in class %(classname)!" % {'name':name, 'classname':self.name}
            return None
        else:
            return ff.to_lcm_callback(prefix)

    def codegen(self):
        self.to_structs_h()
        self.to_structs_lcm()

    def _filter_structs(self, structs):
        outstructs = []
        for struct in structs:
            if struct.tag == 'message' or struct.tag == 'struct':
                struct.attrib['cl'] = self
                outstructs.append(LCMStruct(struct, self.name))
            elif struct.tag == 'enum':
                struct.attrib['cl'] = self
                outstructs.append(LCMEnum(struct, self.name))
            else:
                print baseio.parse_type_error % {"msg_tag":struct.tag, "filename":"types"}
        return outstructs

    def include_headers(self):
        return "\n".join(["#include \"" + genconfig.lcm_folder + "/" 
                          + self.name + "_" + x.name + 
                          ".h\"\n" for x in self.structs])

    def to_structs_h(self):
        def structs_f(cf):
            cf.write("#include <stdint.h>\n\n");
            for s in self.structs:
                # print "writing" , s.name
                cf.write(s.to_c())
                cf.write("\n");
        self.to_h(self.name + "_types", structs_f)
        
    def to_structs_lcm(self):
        def structs_f(cf):
            for s in self.structs:
                cf.write(s.to_lcm())
                cf.write("\n")
        self.to_lcm(self.name, structs_f)
    
