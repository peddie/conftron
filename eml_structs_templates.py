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


############  LCM  ###############
eml_lcm_send_template = """\
function %(classname)s_lcm_send_%(type)s( %(type)s_in_ ) %%#eml

%(type)s_ = %(classname)s_%(type)s( %(type)s_in_, [1,1] );

eml.ceval('emlc_lcm_send_%(type)s', eml.rref(%(type)s_));

end
"""

eml_lcm_send_dummy_template = """\
function %(classname)s_lcm_send_%(type)s( %(type)s_in_ ) %%#eml

%% dummy file to keep simulink from choking

end
"""

#############  STRUCTS  #################
eml_constructor_template = ["""\
function %(type)s_out_ = %(classname)s_%(type)s(%(type)s_in_, n) %%#eml

%% constructor:
""",
"""
if nargin == 0
    return;
end

%% safecopy:
if nargin == 1
    n = [1,1];
end

assert(isequal(size(%(type)s_in_), n));

%(type)s_out_full_ = repmat( %(type)s_out_, n );

for k=1:prod(n)
""",
"""\
end

end\
"""]


#################  ENUMS  ####################
eml_enum_constructor_template = """\
function val_out = %(classname)s_%(type)s(val_in, n) %%#eml

if nargin == 0
    val_out = int32(0);
    return;
end

%% arrays of enums not yet supported
if nargin == 2
    assert(n == [1,1]);
end

if ischar(val_in)
    val_out = encode_%(classname)s_%(type)s(val_in);
else
    assert(isinteger(val_in));
    assert(isscalar(val_in));
    val_out = int32(val_in);
end

end
"""


eml_enum_encoder_template_0 = """\
function int32_out = encode_%(classname)s_%(type)s(string_in); %%#eml

assert(ischar(string_in));

switch string_in
"""

eml_enum_encoder_template_1 = """\
    otherwise
        error_string = sprintf(\'unrecognized enum string value \'\'%%s\'\' in encode_%(classname)s_%(type)s\\n\', string_in);
        error(error_string);
end

end\
"""

eml_enum_decoder_template_0 = """\
function string_out = decode_%(classname)s_%(type)s(int_in); %%#eml

assert(isnumeric(int_in));

switch int32(int_in)
"""

eml_enum_decoder_template_1 = """\
    otherwise
        error_string = sprintf(\'unrecognized enum integer value \'\'%%d\'\' in decode_%(classname)s_%(type)s\\n\', int_in);
        error(error_string);
end

end\
"""
