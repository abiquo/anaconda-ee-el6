/*
 * hardware.h
 *
 * Copyright (C) 2007  Red Hat, Inc.  All rights reserved.
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

#ifndef LOADERHW_H
#define LOADERHW_H

#include "modules.h"

/*
  USB and SCSI subsystems have 1s delay loop to allow for all their devices
  to settle before enumerating. We have to wait too after udev settles, because
  we are missing those devices otherwise.
*/
#define USB_DETECT_DELAY 2

int earlyModuleLoad(int justProbe);

/* does explicit hardware detection with configurable delay after
   udev finishes it's stuff */
int detectHardware(int delay);

#endif
