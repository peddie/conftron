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

import genconfig, sys, collections
from xml.etree import ElementTree as ET
import xml.parsers.expat as expat

h_file_head = """
/* This file is part of conftron.  
 * 
 * Copyright (C) 2011 Matt Peddie <peddie@jobyenergy.com>
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
 * 02110-1301, USA.
 *
 * ==================================================================
 * This file is automatically generated by lcmgen.py.  Do not edit it
 * yourself!  Instead, change the XML configuration that informs the
 * generation process.  
 * ==================================================================
 */
"""

parse_type_error = """
Warning: XML parser encountered an object of type `%(msg_tag)s' 
in file `%(filename)s.'  Either the XML is broken 
(check for typos?) or support for this type is not yet implemented.
"""

include_type_error = """
Warning!  Use of <include .../> directive in XML config file may have
resulted in an inconsistent configuration (in object %(repr)s
`%(name)s').  This object expected subelements of type `%(ok)s', but
after parsing XML, it ended up with a subelement of type `%(bad)s'.  
"""
## Utility parent classes that let you write properly formed C, Octave
## and LCM files.
class CHeader():
    def __init__(self):
        pass

    def to_h(self, name, output_f):
        cf = open(name + ".h", 'w')
        cf.write(h_file_head + "\n")
        hname = name.replace("/", "_").upper()
        cf.write("#ifndef __" + hname + "_H__\n")
        cf.write("#define __" + hname + "_H__\n\n")
        output_f(cf)
        cf.write("\n\n#endif // __" + hname + "_H__\n")
        cf.close()
        # print "Autogenerated file `" + name + ".h'."

    def cpp_wrap(self, strin):
        return """
#ifdef __cplusplus
extern "C"{
#endif

%(str)s

#ifdef __cplusplus
}
#endif
""" % {"str":strin}

class CCode():
    def __init__(self):
        pass
    def to_c(self, name, output_f):
        def tmp_output_f(cf):
            cf.write("#include \"" + name + ".h\"\n\n")
            output_f(cf)
        self.to_c_no_h(name, tmp_output_f)

    def to_c_no_h(self, name, output_f):
        cf = open(name + ".c", "w")
        cf.write(h_file_head + "\n")
        output_f(cf)
        cf.close()
        # print "Autogenerated file `" + name + ".c'."

class OctaveCode():
    def __init__(self):
        pass
    def to_octave_code(self, name, output_f):
        cf = open(name + ".m", "w")
        output_f(cf)
        cf.close()
        # print "Autogenerated file `" + name + ".m'."

class LCMFile():
    def __init__(self):
        pass
 
    def to_lcm(self, name, output_f):
        lf = open(name + ".lcm", 'w')
        lf.write(h_file_head + "\n")
        lf.write("package " + name + ";\n")
        output_f(lf)
        lf.close()
        # print "Autogenerated file `" + name + ".lcm'."
   
class ImADictionary():
    def __init__(self):
        pass
    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)

    def has_key(self, key):
        try:
            getattr(self, key)
        except AttributeError:
            return False
        else:
            return True

class TagInheritance(ImADictionary):
    reserved = genconfig.reserved_tag_names
    def __init__(self):
        pass

    def _inherit(self, parent):
        for tag, value in parent.__dict__.iteritems():
            if not tag in self.__dict__ and not tag in self.reserved:
                if not self.has_key(tag):
                    self[tag] = value

    def _musthave(self, parent, errmsg):
        for tag in self.required_tags:
            if not self.has_key(tag):
                if not parent.has_key(tag):
                    print errmsg % dict(self, **{'tag':tag})
                self[tag] = parent[tag]

class Searchable():
    def __init__(self):
        pass

    def _search(self, collection, searchname):
        try:
            return (i for i in collection if i.name == searchname).next()
        except StopIteration:
            return None

    def _recsearch(self, collection, searchname):
        try:
            return (i for i in collection if i.name == searchname).next()
        except StopIteration:
            try:
                return (i.search(searchname) for i in collection if i.search(searchname)).next()
            except StopIteration:
                return None

    def _dictsearch(self, dictionary, searchname):
        if dictionary.has_key(searchname):
            return dictionary[searchname]

    def _dictrecsearch(self, dictionary, searchname):
        if dictionary.has_key(searchname):
            return dictionary[searchname]
        else:
            return (v for k,v in dictionary.iteritems() if v.search(searchname)).next()

class IncludePasting():
    def __init__(self):
        pass

    def flatten_list(self, x):
        result = []
        for el in x:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                result.extend(self.flatten_list(el))
            else:
                result.append(el)
        return result

    def include(self, child, ok):
        if child.tag == 'include':
            try:
                includename = self.path + child.attrib['href']
                return ET.ElementTree().parse(includename).getchildren()
            except IOError as e:
                print "Couldn't open included XML file `" + includename +"':", e
                self.die = True
            except expat.ExpatError as e:
                print "Error parsing included XML file `" + includename +"':", e
                self.die = True
        elif not child.tag in ok:
            print parse_type_error % {'msg_tag':child.tag, 'filename':self.file}
        else:
            return child

    def insert_includes(self, children, ok):        
        self.die=False
        out = [self.include(c, ok) for c in children]
        if self.die:
            print "XML parsing encountered one or more fatal errors; exiting."
            sys.exit(1)
        return self.flatten_list(out)
            
    def check_includes(self, children, ok):
        fail = False
        for c in children:
            if not c.tag in ok:
                print include_type_error % {'repr':repr(self), 'name':self.name, 'ok':ok, 'bad':c.tag}
                fail = True
        if fail: 
            print
            print "I will try to continue, but if you experience problems, check your use of XML <include>s."
