/*
 * shutdown.c
 *
 * Shutdown a running system.  If built with -DAS_SHUTDOWN=1, then
 * it builds a standalone shutdown binary.
 *
 * Copyright (C) 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003  Red Hat, Inc.
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/reboot.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include "init.h"

void disableSwap(void);
void unmountFilesystems(void);

static void performTerminations(void) {
    /* First of all kill everything in the anaconda process group. This won't
       hit any daemons spawned from anaconda, those usually call setsid(). */
    char buf[256];
    int fd, anaconda_pid = 0;
    if ((fd = open("/var/run/anaconda.pid", O_RDONLY)) >= 0 ) {
        if (read(fd, buf, 256) > 0) {
            anaconda_pid = atol(buf);
        }
    }
    if (anaconda_pid > 0) {
        printf("terminating anaconda...");
        kill(-anaconda_pid, SIGTERM);
        printf("done\n");
    }

    /* Next, kill everything except what is inside the init's session or
       excluded in donotkill. */
    FILE *f;
    char *donotkill[] = {"mdmon", "NetworkManager", "dhclient", NULL};
    char omit[256], oarg[64];
    char **procname, *pid;

    /* find some pids so we can omit them from killall5 */
    *omit = '\0';
    for (procname=donotkill; *procname; procname++) {
        sprintf(buf, "/usr/sbin/pidof %s", *procname);
        if ((f = popen(buf, "r")) != NULL) {
            if (fgets(buf, sizeof(buf), f) != NULL) {
                buf[strcspn(buf,"\n")] = '\0';
                pid = strtok(buf, " ");
                while (pid) {
                    sprintf(oarg, " -o %s", pid);
                    strcat(omit, oarg);
                    pid = strtok(NULL, " ");
                }
            }

            fclose(f);
        }
    }

    int status;
    sync();
    printf("sending termination signals...");
    fflush(stdout);
    sprintf(buf, "/usr/sbin/killall5 -15%s", omit);
    status = system(buf);
    sleep(2);
    printf("done\n");

    printf("sending kill signals...");
    fflush(stdout);
    sprintf(buf, "/usr/sbin/killall5 -9%s", omit);
    status = system(buf);
    sleep(2);
    printf("done\n");
}

static void performUnmounts(void) {
	int status;
	struct stat st_buf;

	printf("disabling swap...\n");
	disableSwap();

	/* We'll lose /mnt/runtime where /lib is a link to put the old
	   /lib back so that our mdadm invocation below works. */
	if (stat("/lib64", &st_buf) == 0) {
		unlink("/lib64");
		rename("/lib64_old", "/lib64");
	} else {
		unlink("/lib");
		rename("/lib_old", "/lib");
	}
	unlink("/usr");
	rename("/usr_old", "/usr");

	printf("unmounting filesystems...\n"); 
	unmountFilesystems();

	printf("waiting for mdraid sets to become clean...\n"); 
	status = system("/sbin/mdadm --wait-clean --scan");
	if (!WIFEXITED(status))
		printf("Error: mdadm did not terminate normally\n");
	else if (WEXITSTATUS(status))
		printf("Error: mdadm exited with status: %d\n",
		       WEXITSTATUS(status));
}

static void performReboot(reboot_action rebootAction) {
    switch (rebootAction) {
    case POWEROFF:
        printf("powering off system\n");
        sleep(2);
        reboot(RB_POWER_OFF);
        break;
    case REBOOT:
        printf("rebooting system\n");
        sleep(2);
#if USE_MINILIBC
        reboot(0xfee1dead, 672274793, 0x1234567);
#else
        reboot(RB_AUTOBOOT);
#endif
        break;
    case HALT:
        printf("halting system\n");
        reboot(RB_HALT_SYSTEM);
        break;
    default:
        break;
    }
}

static void performDelayedReboot()
{
    printf("The system will be rebooted when you press Ctrl-C or Ctrl-Alt-Delete.\n");
    while (1) {
        sleep(1);
    }
}

void shutDown(int doKill, reboot_action rebootAction)
{
    static int reentered = 0;
    
    if (reentered) {
        performTerminations();
        performUnmounts();
        performReboot(rebootAction);
    }
    reentered = 1;
    if (rebootAction != DELAYED_REBOOT && doKill) {
        performTerminations();
        performUnmounts();
        performReboot(rebootAction);
    } else {
        performDelayedReboot();
    }
    exit(0);
}

#ifdef AS_SHUTDOWN
int main(int argc, char ** argv) {
    int fd;
    reboot_action rebootAction = HALT;
    int doKill = 1;
    int i = 1;

    while (i < argc) {
      if (!strncmp("-r", argv[i], 2))
        rebootAction = REBOOT;
      else if (!strncmp("--nokill", argv[i], 8))
        doKill = 0;
      else if (!strncmp("-P", argv[i], 2))
        rebootAction = POWEROFF;
      i++;
    }

    /* ignore some signals so we don't kill ourself */
    signal(SIGINT, SIG_IGN);
    signal(SIGTSTP, SIG_IGN);

    /* now change to / */
    i = chdir("/");

    /* redirect output to the real console */
    fd = open("/dev/console", O_RDWR);
    dup2(fd, 0);
    dup2(fd, 1);
    dup2(fd, 2);
    close(fd);

    shutDown(doKill, rebootAction);
    return 0;
}
#endif

/* vim:set shiftwidth=4 softtabstop=4 ts=4: */
