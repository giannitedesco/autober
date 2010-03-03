#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <gber.h>
#include <autober.h>
#include "bio_group.h"

static const struct autober_tag root_tags[] = {
	{.ab_label = "Biometric Information Group Template",
		.ab_tag = TAG_BIO_GROUP,
		.ab_flags = AUTOBER_TEMPLATE},
};

static const struct autober_tag bio_group_tags[] = {
	{.ab_label = "num_instances",
		.ab_tag = TAG_BIO_GROUP_NUM_INSTANCES,
		.ab_count = {1,},
		.ab_type = AUTOBER_TYPE_INT},
	{.ab_label = "bio_inf",
		.ab_label = "Biometric 'Information' Template",
		.ab_tag = TAG_BIO_GROUP_BIO_INF,
		.ab_flags = AUTOBER_TEMPLATE | AUTOBER_SEQUENCE,},
};

static const struct autober_tag bio_inf_tags[] = {
	{.ab_label = "Biometric Header Template",
		.ab_tag = TAG_BIO_INF_BIO_HDR,
		.ab_flags = AUTOBER_TEMPLATE},
	{.ab_label = "bdb.bdb_nc",
		.ab_tag = TAG_BIO_INF_BDB_NC,
		.ab_flags = AUTOBER_UNION},
	{.ab_label = "bdb.bdb_c",
		.ab_tag = TAG_BIO_INF_BDB_C,
		.ab_flags = AUTOBER_UNION},
};

static const struct autober_tag bio_hdr_tags[] = {
	{.ab_label = "vers",
		.ab_tag = TAG_BIO_HDR_VERS,
		.ab_count = {2,},
		.ab_type = AUTOBER_TYPE_INT},
	{.ab_label = "type",
		.ab_tag = TAG_BIO_HDR_TYPE,
		.ab_count = {2,3},
		.ab_type = AUTOBER_TYPE_OCTET|AUTOBER_OPTIONAL},
	{.ab_label = "subtype",
		.ab_tag = TAG_BIO_HDR_SUBTYPE,
		.ab_count = {2,},
		.ab_type = AUTOBER_TYPE_INT|AUTOBER_OPTIONAL},
	{.ab_label = "date",
		.ab_tag = TAG_BIO_HDR_DATE,
		.ab_count = {7,7},
		.ab_type = AUTOBER_TYPE_OCTET|AUTOBER_OPTIONAL},
	{.ab_label = "validty",
		.ab_tag = TAG_BIO_HDR_VALIDITY,
		.ab_count = {8,8},
		.ab_type = AUTOBER_TYPE_OCTET|AUTOBER_OPTIONAL},
	{.ab_label = "creator_pid",
		.ab_tag = TAG_BIO_HDR_CREATOR_PID,
		.ab_count = {2,2},
		.ab_type = AUTOBER_TYPE_OCTET|AUTOBER_OPTIONAL},
	{.ab_label = "format_owner",
		.ab_tag = TAG_BIO_HDR_FORMAT_OWNER,
		.ab_count = {2,2},
		.ab_type = AUTOBER_TYPE_OCTET},
	{.ab_label = "format_type",
		.ab_tag = TAG_BIO_HDR_FORMAT_TYPE,
		.ab_count = {2,2},
		.ab_type = AUTOBER_TYPE_OCTET},
};

static void *do_free(struct bio_group *bio_group)
{
	if ( bio_group ) {
		free(bio_group->bio_inf);
		free(bio_group);
	}

	return NULL;
}

static int _bio_hdr(struct bio_hdr *bio_hdr,
				const uint8_t *ptr, size_t len)
{
	static const unsigned int num = AUTOBER_NUM_TAGS(bio_hdr_tags);
	struct autober_constraint cons[num];
	struct gber_tag tag;
	const uint8_t *end;

	if ( !autober_constraints(bio_hdr_tags, cons, num, ptr, len) ) {
		fprintf(stderr, "bio_hdr_tags: constraints not satisified\n");
		return 0;
	}

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_HDR_VERS:
			break;
		case TAG_BIO_HDR_TYPE:
			bio_hdr->_present |= BIO_HDR_TYPE;
			break;
		case TAG_BIO_HDR_SUBTYPE:
			bio_hdr->_present |= BIO_HDR_SUBTYPE;
			break;
		case TAG_BIO_HDR_DATE:
			bio_hdr->_present |= BIO_HDR_DATE;
			break;
		case TAG_BIO_HDR_VALIDITY:
			bio_hdr->_present |= BIO_HDR_VALIDITY;
			break;
		case TAG_BIO_HDR_CREATOR_PID:
			bio_hdr->_present |= BIO_HDR_CREATOR_PID;
			break;
		case TAG_BIO_HDR_FORMAT_OWNER:
			break;
		case TAG_BIO_HDR_FORMAT_TYPE:
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return 0;
		}
	}

	return 1;
}

static int _bio_inf(struct bio_inf *bio_inf,
				const uint8_t *ptr, size_t len)
{
	static const unsigned int num = AUTOBER_NUM_TAGS(bio_inf_tags);
	struct autober_constraint cons[num];
	struct gber_tag tag;
	const uint8_t *end;

	if ( !autober_constraints(bio_inf_tags, cons, num, ptr, len) ) {
		fprintf(stderr, "bio_inf_tags: constraints not satisified\n");
		return 0;
	}

	if ( cons[1].count == 0 && cons[2].count == 0 ) {
		fprintf(stderr, "bio_inf: one or more union "
			"members must be set\n");
		return 0;
	}

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_INF_BIO_HDR:
			_bio_hdr(&bio_inf->bio_hdr, ptr, tag.ber_len);
			break;
		case TAG_BIO_INF_BDB_NC:
			break;
		case TAG_BIO_INF_BDB_C:
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return 0;
		}
	}

	return 1;
}

static int _bio_group(struct bio_group *bio_group,
				const uint8_t *ptr, size_t len)
{
	static const unsigned int num = AUTOBER_NUM_TAGS(bio_group_tags);
	struct autober_constraint cons[num];
	struct gber_tag tag;
	const uint8_t *end;

	if ( !autober_constraints(bio_group_tags, cons, num, ptr, len) ) {
		fprintf(stderr, "bio_group_tags: constraints not satisified\n");
		return 0;
	}

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_GROUP_NUM_INSTANCES:
			break;
		case TAG_BIO_GROUP_BIO_INF:
			bio_group->bio_inf = calloc(cons[1].count,
						sizeof(*bio_group->bio_inf));
			if ( NULL == bio_group->bio_inf )
				return 0;

			if ( !_bio_inf(bio_group->bio_inf + cons[1].len,
					ptr, tag.ber_len) )
				return 0;
			cons[1].len++;
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return 0;
		}
	}

	return 1;
}

struct bio_group *bio_group_decode(const uint8_t *ptr, size_t len)
{
	static const unsigned int num = AUTOBER_NUM_TAGS(root_tags);
	struct autober_constraint cons[num];
	struct bio_group *ret;
	struct gber_tag tag;
	const uint8_t *end;

	if ( !autober_constraints(root_tags, cons, num, ptr, len) ) {
		fprintf(stderr, "root_tags: constraints not satisified\n");
		return NULL;
	}

	ret = calloc(1, sizeof(*ret));
	if ( NULL == ret )
		return NULL;

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return do_free(ret);

		switch(tag.ber_tag) {
		case TAG_BIO_GROUP:
			if ( !_bio_group(ret, ptr, tag.ber_len) )
				return do_free(ret);
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return do_free(ret);
		}
	}

	return ret;
}

void bio_group_free(struct bio_group *bio_group)
{
	do_free(bio_group);
}