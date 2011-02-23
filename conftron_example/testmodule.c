/* Simple test module for new LCM/autogeneration system */
#include <ap_types.h>
#include AIRFRAME_CONSTANTS

static xyz_t foobar = FOOBAR_INIT;
#include <settings/ap_xyz_t_foobar.h>

int
test_module_report(void)
{
  foobar.x++;
  foobar.y++;
  foobar.z++;
  return foobar.x + foobar.y + foobar.z;
}
