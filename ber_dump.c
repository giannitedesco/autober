#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <ctype.h>
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

static void hex_dump(const uint8_t *tmp, size_t len,
			size_t llen, unsigned int depth)
{
	size_t i, j;
	size_t line;

	for(j = 0; j < len; j += line, tmp += line) {
		if ( j + llen > len ) {
			line = len - j;
		}else{
			line = llen;
		}

		printf("%*c%05x : ", depth, ' ', j);

		for(i = 0; i < line; i++) {
			if ( isprint(tmp[i]) ) {
				printf("%c", tmp[i]);
			}else{
				printf(".");
			}
		}

		for(; i < llen; i++)
			printf(" ");

		for(i=0; i < line; i++)
			printf(" %02x", tmp[i]);

		printf("\n");
	}
	printf("\n");
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

static int ber_dump(const uint8_t *ptr, size_t len, unsigned int depth)
{
	const uint8_t *end = ptr + len;

	while(ptr < end) {
		struct gber_tag tag;
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		printf("%*c.tag: %x\n", depth, ' ', tag.ber_tag);
		printf("%*c o class: %s\n", depth, ' ',
			ber_id_octet_clsname(tag.ber_id));
		printf("%*c o constructed: %s\n", depth, ' ',
			ber_id_octet_constructed(tag.ber_id) ? "yes" : "no");

		printf("%*c.len = %u (0x%.2x)\n",
			depth, ' ', tag.ber_len, tag.ber_len);

		if ( ber_id_octet_constructed(tag.ber_id) ) {
			if ( !ber_dump(ptr, tag.ber_len, depth + 1) )
				return 0;
		}else{
			hex_dump(ptr, tag.ber_len, 16, depth + 1);
		}

		ptr += tag.ber_len;
	}

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

	if ( !ber_dump(map, sz, 0) ) {
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
