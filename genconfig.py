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

## Basic configuration for the code generation setup

from os import environ

ap_project_root = environ.get("AP_PROJECT_ROOT")

sim_flag = "SIMULATOR_COMPILE_FLAG"
timestep = "DT"
telemetry_folder = "telemetry"
settings_folder = "settings"
lcm_folder = "auto"
lcm_basic = "lcm_telemetry_new"
stubs_folder = "stubs"
config_folder = ap_project_root + "/conf/"
airframe_config_folder = config_folder + "airframes/"
lcm_settings_autogen = "lcm_settings_auto"
lcm_telemetry_autogen = "lcm_telemetry_auto"
classes_file = "classes.dat"

