/*
 * mkctype.c
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

#include <ctype.h>
#include <stdio.h>

#if __GLIBC__ > 2 || (__GLIBC__ == 2 && __GLIBC_MINOR__ > 2)
# define __ctype_b (*__ctype_b_loc())
# define __ctype_tolower (*__ctype_tolower_loc())
# define __ctype_toupper (*__ctype_toupper_loc())
#endif

int main(int argc, char ** argv) {
    int i;

    printf("#include <sys/types.h>\n\n");

    printf("static const unsigned short int __ctype_b_internal[] = {");

    for (i = -128; i < 256; i++) {
	if (!(i % 8)) {
	    printf("\n");
	}

	printf("\t0x%x,", __ctype_b[i]);
    }

    printf("\n};\n\n");
    printf("const unsigned short int * __ctype_b = __ctype_b_internal + 128;\n\n");

    printf("const int __ctype_toupper_internal[] = {");
    for (i = -128; i < 256; i++) {
	if (!(i % 8)) {
	    printf("\n");
	}

	printf("\t0x%x,", __ctype_toupper[i]);
    }

    printf("\n};\n\n");
    printf("const int * __ctype_toupper = __ctype_toupper_internal + 128;\n\n");

    printf("const int __ctype_tolower_internal[] = {");
    for (i = -128; i < 256; i++) {
	if (!(i % 8)) {
	    printf("\n");
	}

	printf("\t0x%x,", __ctype_tolower[i]);
    }

    printf("\n};\n\n");
    printf("const int * __ctype_tolower = __ctype_tolower_internal + 128;\n\n");

    printf ("const unsigned short int **__ctype_b_loc (void) { return &__ctype_b; }\n");
    printf ("const int **__ctype_toupper_loc (void) { return &__ctype_toupper; }\n");
    printf ("const int **__ctype_tolower_loc (void) { return &__ctype_tolower; }\n\n");

    return 0;
};
