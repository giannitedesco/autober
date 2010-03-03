#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#include <gber.h>
#include <autober.h>
#include "bio_group.h"

static const char *cmd;
static const char *sys_err(void)
{
	return strerror(errno);
}

static int mapfile(int fd, const uint8_t **begin, size_t *sz)
{
	struct stat st;

	if ( fstat(fd, &st) )
		return 0;

	*begin = mmap(NULL, st.st_size, PROT_READ,
			MAP_SHARED, fd, 0);

	if ( *begin == MAP_FAILED )
		return 0;

	*sz = st.st_size;

	return 1;
}

static int parse_dg2(const uint8_t *ptr, size_t len)
{
	struct bio_group *bio;
	struct gber_tag tag;

	ptr = ber_decode_tag(&tag, ptr, len);
	if ( NULL == ptr )
		return 0;
	
	if ( tag.ber_tag != 0x75 ) {
		fprintf(stderr, "Expected tag 0x75 but got 0x%x", tag.ber_tag);
		return 0;
	}

	bio = bio_group_decode(ptr, tag.ber_len);
	if ( NULL == bio )
		return 0;

	bio_group_free(bio);
	return 1;
}

static int do_file(char *fn, int fd)
{
	const uint8_t *map;
	size_t sz;
	int ret = 1;

	printf("%s: processing file: %s\n", cmd, fn);
	if ( !mapfile(fd, &map, &sz) ) {
		fprintf(stderr, "%s: mapfile: %s\n", cmd, sys_err());
		return 0;
	}

	ret = parse_dg2(map, sz);
	munmap((void *)map, sz);
	printf("\n");
	return ret;
}

int main(int argc, char **argv)
{
	int files = 0;

	cmd = argv[0];

	if ( argc < 2 )  {
		if ( do_file("(stdin)", STDIN_FILENO) )
			files++;
	}else{
		int i;
		for(i = 1; i < argc; i++) {
			int fd;

			fd = open(argv[i], O_RDONLY);
			if ( fd < 0 ) {
				fprintf(stderr, "%s: open: %s", cmd, sys_err());
				continue;
			}

			if ( do_file(argv[i], fd) )
				files++;

			close(fd);
		}
	}

	return (files) ? EXIT_SUCCESS : EXIT_FAILURE;
}
