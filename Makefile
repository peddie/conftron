## Conftron makefile.  
## -Wunused-parameter.
UNAME := $(shell uname)

SRC = lcm_interface.c 
SRC += $(shell ls *_telemetry.c)

LCM_TYPES = $(shell cat classes.dat | perl -pe "s/(\w+) /\1.lcm /gi;" 2>/dev/null)
SRC += $(shell ./types.sh $(LCM_TYPES))

OBJ = $(SRC:%.c=%.o)

INCLUDES += -I.
LDFLAGS += -llcm

XML = types.xml telemetry.xml settings.xml
XML_PATH = conf/

AP_PROJECT_ROOT ?= ..

WARNINGFLAGS = -Wall -Wextra -Werror -std=gnu99
AUTOFLAGS = -Wno-unused-parameter
DEBUGFLAGS = -g -DDT=0.01
OPTFLAGS = 

LIBSRC = $(shell ls stubs/*stub.c)
LIBOBJ = $(LIBSRC:%.c=%.o)
LIBNAME = libautostubs
LIBFLAGS = -fpic 
MKLIBFLAGS = -shared -Wl,-soname,$(LIBNAME).so

ifeq ($(UNAME),Darwin)
	LDFLAGS += -L/usr/local/lib
	INCLUDES += -isystem /usr/local/include
else
OPTFLAGS += -march=native -O3 
endif

CFLAGS ?= $(WARNINGFLAGS) $(DEBUGFLAGS) $(INCLUDES) $(OPTFLAGS) -DAIRFRAME_CONSTANTS=\<airframes/$(aircraft).h\>

Q ?= @

.PHONY: all clean tidy megaclean

## The author apologizes for the `all' make target, also known as
## LAMBDA: THE ULTIMATE MONAD (with apologies to Steele, Peyton-Jones
## and many others).  His make skills are not strong.  
all: 
	$(Q)$(MAKE) -C . clean
	$(Q)$(MAKE) -C . gen
	$(Q)$(MAKE) -C . compile -j

engage: all

lcm:
	$(Q)lcm-gen -c $(LCM_TYPES) --c-cpath auto/ --c-hpath auto/
	$(Q)lcm-gen -p $(LCM_TYPES) --ppath .

gen: 
	@echo
	@echo ----- Generating LCM types and custom C interface. -----
	@echo
	$(Q)python lcmgen.py $(AP_PROJECT_ROOT)/$(XML_PATH)/airframes/$(AIRCRAFT).xml 
	$(Q)$(MAKE) -C . lcm
	@echo
	@echo ----- Done generating code.  -----
	@echo

# This builds a shared library. 
# $(Q)$(CC) $(CFLAGS) $(MKLIBFLAGS) $< -o $(LIBNAME).so
lib: $(LIBOBJ)
	@echo AR $(LIBNAME).a
	$(Q)$(AR) rcs $(LIBNAME).a $(LIBOBJ)
	$(Q)rm *stub.o &>/dev/null || echo
	@echo LIBCC $(LIBNAME).so

compile: lib $(OBJ) 

stubs/%stub.o : stubs/%stub.c
	@echo LIBCC $@
	$(Q)$(CC) -c $(CFLAGS) $(LIBFLAGS) $< -o $@

%.o : auto/%.c 
	@echo CC $@
	$(Q)$(CC) -c $(CFLAGS) $(AUTOFLAGS) $< 

%.o : %.c
	@echo CC $@
	$(Q)$(CC) -c $(CFLAGS) $<

%.o : telemetry/%.c 
	@echo CC $@
	$(Q)$(CC) -c $(CFLAGS) $<

%.o : settings/%.c
	@echo CC $@
	$(Q)$(CC) -c $(CFLAGS) $<

upstream: 
	$(Q)cd upstream; \
	./configure; \
	$(MAKE); \
	sudo $(MAKE) install; \
	sudo ldconfig || echo "no ldconfig found; hope you're on a mac"; 

test: test.o testmodule.o $(OBJ) 
	$(CC) -o $@ $(CFLAGS) $?

tidy: 
	rm -f *.o *~ *.s; 

clean: tidy
	./clean.sh &>/dev/null
	rm -f test

old: 
	@echo Generating autopilot LCM types . . . 
	$(Q)python python_class_from_header.py path_follower_commands sim_commands
	$(Q)lcm-gen -c $(LCM_TYPES) --c-cpath auto/ --c-hpath auto/
	$(Q)lcm-gen -p $(LCM_TYPES) --ppath .

megaclean:
	$(MAKE) -C upstream clean
