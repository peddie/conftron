#!/bin/bash

lcm-gen -d ${@} | grep struct | perl -pe "s/^struct\s+(\w+)\.(\w+)\s+.*$/\1_\2.c/gi;"
