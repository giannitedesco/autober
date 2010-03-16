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
#include <assert.h>
#include <ctype.h>
#include <endian.h>
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

#define _packed __attribute__((packed))
struct fac_hdr {
	uint8_t magic[4];
	uint8_t vers[4];
	uint32_t reclen;
	uint16_t num_img;
	uint32_t block_len;
	uint16_t num_features;
	uint8_t gender;
	uint8_t eye_color;
	uint8_t hair_color;
	uint8_t feature_mask[3];
	uint16_t expression;
	uint8_t pose_angle[3];
	uint8_t pose_angle_uncertainty[3];
}_packed;

struct img_hdr {
	uint8_t type;
	uint8_t dtype;
	uint16_t width;
	uint16_t height;
	uint8_t color_space;
	uint8_t source_type;
	uint8_t device_type[3];
	uint8_t quality;
}_packed;

static int parse_fac(unsigned int i, const uint8_t *ptr, size_t len)
{
	const uint8_t *end = ptr + len;
	struct fac_hdr *fac;
	struct img_hdr *img;
	char fn[32];
	int fd;

	fac = (struct fac_hdr *)ptr;
	ptr += sizeof(*fac);
	if ( ptr > end ) {
		fprintf(stderr, "bio_inf[%u].bdb: Truncated\n", i);
		return 0;
	}

	if ( memcmp(fac->magic, "FAC", sizeof(fac->magic)) ) {
		fprintf(stderr, "bio_inf[%u].bdb: Bad magic\n", i);
		return 0;
	}

	printf("bio_inf[%u].bdb: FAC version: %.*s\n", i,
		sizeof(fac->vers), fac->vers);

	printf("bio_inf[%u].bdb: %u features\n", i,
		htobe16(fac->num_features));
	
	ptr += htobe16(fac->num_features) * 8;
	if ( ptr > end ) {
		fprintf(stderr, "bio_inf[%u].bdb: Truncated\n", i);
		return 0;
	}

	img = (struct img_hdr *)ptr;
	ptr += sizeof(*img);
	if ( ptr > end ) {
		fprintf(stderr, "bio_inf[%u].bdb: Truncated\n", i);
		return 0;
	}

	snprintf(fn, sizeof(fn), "ef.dg2.image.%d.jpeg", i);
	fd = open(fn, O_WRONLY|O_CREAT|O_TRUNC, 0600);
	if ( fd < 0 )
		return 0;
	if ( write(fd, ptr, end - ptr) != (end - ptr) ) {
		close(fd);
		return 0;
	}
	close(fd);
	printf("bio_inf[%u].bdb: written to %s\n", i, fn);
	return 1;
}

static void print_bio_group(struct bio_group *bg)
{
	unsigned int i;

	assert(bg->num_instances == bg->_bio_inf_count);

	printf("bio_group.num_instances = %u\n", bg->num_instances);
	for(i = 0; i < bg->num_instances; i++) {
		struct bio_inf *bi;
		struct bio_hdr *bh;

		bi = bg->bio_inf + i;
		bh = &bi->bio_hdr;
		printf("bio_inf[%u].hdr.vers = 0x%.4x\n", i, bh->vers);
		if ( bh->_present & BIO_HDR_TYPE )
			printf("bio_inf[%u].hdr_type = {%.2x, %.2x, %.2x}\n", i,
				bh->type[0],
				bh->type[1],
				bh->type[2]);
		if ( bh->_present & BIO_HDR_SUBTYPE )
			printf("bio_inf[%u].hdr.subtype = 0x%.4x\n", i,
				bh->vers);
		if ( bh->_present & BIO_HDR_DATE)
			printf("bio_inf[%u].hdr_date = "
				"%.2x%.2x-%.2x-%.2x %.2x:%2x:%.2x\n", i,
				bh->date[0],
				bh->date[1],
				bh->date[2],
				bh->date[3],
				bh->date[4],
				bh->date[5],
				bh->date[6]);
		printf("bio_inf[%u].hdr.format_owner = 0x%.4x\n", i,
			(bh->format_owner[0] << 8) |
			bh->format_owner[1]);
		printf("bio_inf[%u].hdr.format_type = 0x%.4x\n", i,
			(bh->format_type[0] << 8) |
			bh->format_type[1]);
		switch(bi->_bdb_type) {
		case BIO_INF_BDB_TYPE_BDB_NC:
			printf("bio_inf[%u].bdb = NONCONSTRUCTED\n", i);
			parse_fac(i, bi->bdb.bdb_c.ptr, bi->bdb.bdb_c.len);
			break;
		case BIO_INF_BDB_TYPE_BDB_C:
			printf("bio_inf[%u].bdb = CONSTRUCTED\n", i);
			ber_dump(bi->bdb.bdb_c.ptr, bi->bdb.bdb_c.len);
			break;
		default:
			break;
		}
	}
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

	print_bio_group(bio);

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
