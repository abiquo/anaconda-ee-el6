/*
   File name: rpmextract.h
   Date:      2009/09/16
   Author:    msivak

   Copyright (C) 2009 Red Hat, Inc.

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.
*/


#ifndef __RPMEXTRACT_H__
#define __RPMEXTRACT_H__

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#define EXIT_BADDEPS 4
#define BUFFERSIZE 1024

/*
  filter function returns 1 - extract file, 0 - skip
  flags is binary accumulated result from provides callbacks
 */
typedef int (*filterfunc)(const char* name, const struct stat *fstat, int flags, void *userptr);

/*
  returns nonzero if the dependency/provides means we should unpack the package
  moreover the results from provides checks are binary orred (|) and passed as flags to filter function
*/
typedef int (*dependencyfunc)(const char* depname, const char* depversion, const uint32_t sense, void *userptr);

int explodeRPM(const char* file,
               filterfunc filter,
               dependencyfunc provides,
               dependencyfunc deps,
               void* userptr);


int matchVersions(const char *version, uint32_t sense, const char *senseversion);

#endif

/* end of rpmextract.h */
