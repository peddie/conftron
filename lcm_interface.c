/* 
 *   lcm_telemetry.c
 *   Copyright 2010 Joby Energy, Inc.
 *   Matt Peddie
 */

#include <sys/time.h>
#include <stdio.h>

#include <lcm/lcm.h>

#include "lcm_interface.h"

void
lcm_initialize(const char *provider, lcm_t **lcm, int *fd)
{
  *lcm = lcm_create(provider);
  if (!*lcm) {
    fprintf(stderr, "ERROR: Cannot create LCM.\n");
  }
  *fd = lcm_get_fileno(*lcm);
}

void
lcm_wait(lcm_t *lcm)
{
  lcm_handle(lcm);
}

#define MAX_MSGS     22       /* after this many, we return to the
                               * program and continue next time.
                               * Careful with this -- it may cause
                               * messages to build up if it's set too
                               * low for the mean message rate. */

void
lcm_check(lcm_t *lcm, int fd)
{
  int maxfd = fd, selectres, iters=0;
  fd_set lcmread;
  FD_ZERO(&lcmread);
  
  /* Don't want to wait for messages forever. */
  struct timeval tv;
  tv.tv_sec = 0;
  tv.tv_usec = 0;
  
  /* Loop on select() until no more messages have arrived or until the
   * MAX_MSGS limit is exceeded. */
  do {
    FD_SET(fd, &lcmread);
    selectres = select(maxfd+1, &lcmread, NULL, NULL, &tv);
    
    /* If a message is ready, dispatch. */
    if (FD_ISSET(fd, &lcmread)) {
      lcm_handle(lcm);
    } 
  } while ((selectres > 0) && (++iters < MAX_MSGS));
}

