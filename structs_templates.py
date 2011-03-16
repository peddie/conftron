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

eml_lcm_send_template = """\
function %(classname)s_lcm_send_%(type)s( %(type)s_in ) %%#eml

%(type)s_ = %(classname)s_safecopy_%(type)s( %(type)s_in, [1,1] );

eml.ceval('emlc_lcm_send_%(type)s', eml.rref(%(type)s_in));

end
"""

eml_lcm_send_dummy_template = """\
function %(classname)s_lcm_send_%(type)s( %(type)s_in ) %%#eml

%% dummy file to keep simulink from choking

end
"""
