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

static int do_file(char *fn, int fd)
{
	const uint8_t *map;
	size_t sz;

	printf("%s: processing file: %s\n", cmd, fn);
	if ( !mapfile(fd, &map, &sz) ) {
		fprintf(stderr, "%s: mapfile: %s\n", cmd, sys_err());
		return 0;
	}

	if ( !ber_dump(map, sz) ) {
		fprintf(stderr, "%s: %s: malformed BER encoding\n", cmd, fn);
	}

	munmap((void *)map, sz);
	printf("\n");
	return 1;
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
