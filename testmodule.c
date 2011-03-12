/* Simple test module for new LCM/autogeneration system */
#include "ap_types.h"

static command_t commando;
/* This is just for lols */
#include <telemetry/ap_command_t_commando.h>

static xyz_t foobar = {2, 2, 2};
#include <settings/ap_xyz_t_foobar.h>

int
test_module_report(void)
{
  foobar.x++;
  foobar.y++;
  foobar.z++;
  return foobar.x + foobar.y + foobar.z;
}
