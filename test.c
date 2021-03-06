/* Simple test program for new LCM/autogeneration system. */

#include <stdio.h>
#include <unistd.h>
#include "lcm_interface.h"

#include "testmodule.h"

int
main(int argc __attribute__((unused)), 
     char **argv __attribute__((unused)))
{
  lcm_init("udpm://239.255.76.67:7667?ttl=0");
  settings_init("udpm://239.255.76.67:7667?ttl=0");
  while(1) {
    telemetry_send();
    lcm_check(ap_lcm.lcm, ap_lcm.fd);
    usleep(1000000 * DT);
    printf("test module says: %d\n", test_module_report());
  }
}
