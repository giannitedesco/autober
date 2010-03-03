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
#include <assert.h>

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

static unsigned int ber_id_octet_class(const uint8_t cls)
{
	return (cls & 0xc0) >> 6;
}

static unsigned int ber_id_octet_constructed(const uint8_t cls)
{
	return (cls & 0x20) >> 5;
}

static unsigned int ber_id_octet_tag(const uint8_t cls)
{
	return cls & 0x1f;
}

static unsigned int ber_len_form_short(const uint8_t cls)
{
	return !(cls & 0x80);
}

static unsigned int ber_len_short(const uint8_t cls)
{
	return cls & ~0x80;
}

static void ber_dump(const uint8_t *buf, size_t len, unsigned int depth)
{
	const uint8_t *end = buf + len;
	unsigned int tag;
	uint32_t clen;
	uint8_t idb;
	static const char * const clsname[]={
		"universal",
		"application",
		"context-specific",
		"private",
	};

again:
	if ( buf >= end )
		return;

	tag = idb = *buf;
	buf++;
	if ( ber_id_octet_tag(idb) == 0x1f) {
		assert(!(*buf & 0x80));
		tag <<= 8;
		tag |= *buf;
		buf++;
	}

	printf("%*c.tag: %x\n", depth, ' ', tag);
	printf("%*c o class: %s\n", depth, ' ',
		clsname[ber_id_octet_class(idb)]);
	printf("%*c o constructed: %s\n", depth, ' ',
		ber_id_octet_constructed(idb) ? "yes" : "no");

	printf("%*c.len = %u (0x%.2x)\n",
		depth, ' ', *buf, *buf);
	printf("%*c o length form: %s\n", depth, ' ',
		ber_len_form_short(*buf) ? "short" : "long");
	if ( ber_len_form_short(*buf) ) {
		clen = ber_len_short(*buf);
		buf++;
	}else{
		uint32_t i, l;

		l = ber_len_short(*buf);
		printf("%*c o length of length: %u\n", depth, ' ', l);
		if ( l > 4 )
			return;
		buf++;
		for(clen = i = 0; i < l; i++, buf++) {
			clen <<= 8;
			clen |= *buf;
		}
	}
	printf("%*c o length: %u\n", depth, ' ', clen);

	if ( ber_id_octet_constructed(idb) ) {
		printf("%*c ----\n", depth, ' ');
		//hex_dump(buf, clen, 16, depth);
		ber_dump(buf, clen, depth + 2);
	}else{
		hex_dump(buf, clen, 16, depth);
	}

	buf += clen;
	goto again;
}

static int mapfile(int fd, const uint8_t **begin, size_t *sz)
{
	struct stat st;

	if ( fstat(fd, &st) ) {
		perror("fstat()");
		return 0;
	}

	*begin = mmap(NULL, st.st_size, PROT_READ,
			MAP_SHARED, fd, 0);

	if ( *begin == MAP_FAILED ) {
		return 0;
	}

	*sz = st.st_size;

	return 1;
}

int main(int argc, char **argv)
{
	const uint8_t *map;
	size_t len;

	if ( !mapfile(STDIN_FILENO, &map, &len) ) {
		fprintf(stderr, "<stdin>: mapfile: %s\n",
			strerror(errno));
		return EXIT_FAILURE;
	}

	ber_dump(map, len, 0);
	return EXIT_SUCCESS;
}
