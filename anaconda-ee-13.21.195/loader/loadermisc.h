/*
 * loadermisc.h
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

#ifndef H_LOADER_MISC_H
#define H_LOADER_MISC_H
#include <stdio.h>
#include <stdarg.h>
#include <glib.h>

#include "windows.h"

#define MEMINFO "/proc/meminfo"

int copyFile(char * source, char * dest);
int copyFileFd(int infd, char * dest, progressCB pbcb,
               struct progressCBdata *data, long long total);
int simpleStringCmp(const void * a, const void * b);
guint64 totalMemory(void);
int replaceChars(char *str, char old, char new);

#endif
