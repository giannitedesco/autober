#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include "gber.h"
#include "autober.h"
#include "bio_group.h"

static const struct autober_tag root_tags[] = {
	{.ab_label = "Biometric Information Group Template",
		.ab_flags = AUTOBER_TEMPLATE,
		.ab_tag = TAG_BIO_GROUP},
};

static const struct autober_tag bio_group_tags[] = {
	{.ab_label = "num_instances",
		.ab_type = AUTOBER_TYPE_INT,
		.ab_flags = AUTOBER_CHECK_SIZE,
		.ab_size = {1, 1},
		.ab_tag = TAG_BIO_GROUP_NUM_INSTANCES},
	{.ab_label = "Biometric 'Information' Template",
		.ab_flags = AUTOBER_TEMPLATE|AUTOBER_SEQUENCE,
		.ab_tag = TAG_BIO_GROUP_BIO_INF},
};

static const struct autober_tag bio_inf_tags[] = {
	{.ab_label = "Biometric Header Template",
		.ab_flags = AUTOBER_TEMPLATE,
		.ab_tag = TAG_BIO_INF_BIO_HDR},
	{.ab_label = "bdb.bdb_nc",
		.ab_type = AUTOBER_TYPE_BLOB,
		.ab_flags = AUTOBER_UNION,
		.ab_tag = TAG_BIO_INF_BDB_NC},
	{.ab_label = "bdb.bdb_c",
		.ab_type = AUTOBER_TYPE_BLOB,
		.ab_flags = AUTOBER_UNION,
		.ab_tag = TAG_BIO_INF_BDB_C},
};

static const struct autober_tag bio_hdr_tags[] = {
	{.ab_label = "vers",
		.ab_type = AUTOBER_TYPE_INT,
		.ab_flags = AUTOBER_CHECK_SIZE,
		.ab_size = {2, 2},
		.ab_tag = TAG_BIO_HDR_VERS},
	{.ab_label = "type",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_OPTIONAL|AUTOBER_CHECK_SIZE,
		.ab_size = {1, 3},
		.ab_tag = TAG_BIO_HDR_TYPE},
	{.ab_label = "subtype",
		.ab_type = AUTOBER_TYPE_INT,
		.ab_flags = AUTOBER_OPTIONAL|AUTOBER_CHECK_SIZE,
		.ab_size = {1, 1},
		.ab_tag = TAG_BIO_HDR_SUBTYPE},
	{.ab_label = "date",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_OPTIONAL|AUTOBER_CHECK_SIZE,
		.ab_size = {7, 7},
		.ab_tag = TAG_BIO_HDR_DATE},
	{.ab_label = "validity",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_OPTIONAL|AUTOBER_CHECK_SIZE,
		.ab_size = {8, 8},
		.ab_tag = TAG_BIO_HDR_VALIDITY},
	{.ab_label = "creator_pid",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_OPTIONAL|AUTOBER_CHECK_SIZE,
		.ab_size = {2, 2},
		.ab_tag = TAG_BIO_HDR_CREATOR_PID},
	{.ab_label = "format_owner",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_CHECK_SIZE,
		.ab_size = {2, 2},
		.ab_tag = TAG_BIO_HDR_FORMAT_OWNER},
	{.ab_label = "format_type",
		.ab_type = AUTOBER_TYPE_OCTET,
		.ab_flags = AUTOBER_CHECK_SIZE,
		.ab_size = {2, 2},
		.ab_tag = TAG_BIO_HDR_FORMAT_TYPE},
};

static void _free_bio_hdr(struct bio_hdr *bio_hdr)
{
}

static void _free_bio_inf(struct bio_inf *bio_inf)
{
	if ( NULL == bio_inf )
		return;

	switch(bio_inf->_bdb_type) {
	case BIO_INF_BDB_TYPE_BDB_C:
		free(bio_inf->bdb.bdb_c.ptr);
		break;
	case BIO_INF_BDB_TYPE_BDB_NC:
		free(bio_inf->bdb.bdb_nc.ptr);
		break;
	}
	_free_bio_hdr(&bio_inf->bio_hdr);
	free(bio_inf);
}

static void _free_bio_group(struct bio_group *bio_group)
{
	unsigned int i;

	if ( NULL == bio_group )
		return;

	for(i = 0; i < bio_group->_bio_inf_count; i++)
		_free_bio_inf(&bio_group->bio_inf[i]);
	free(bio_group);
}

void bio_group_free(struct bio_group *bio_group)
{
	_free_bio_group(bio_group);
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
			if ( !autober_u16(&bio_hdr->vers, &tag, ptr) )
				return 0;
			break;
		case TAG_BIO_HDR_TYPE:
			if ( !autober_octet(bio_hdr->type, &tag, ptr) )
				return 0;
			bio_hdr->_present |= BIO_HDR_TYPE;
			bio_hdr->_type_len = tag.ber_len;
			break;
		case TAG_BIO_HDR_SUBTYPE:
			if ( !autober_u8(&bio_hdr->subtype, &tag, ptr) )
				return 0;
			bio_hdr->_present |= BIO_HDR_SUBTYPE;
			break;
		case TAG_BIO_HDR_DATE:
			if ( !autober_octet(bio_hdr->date, &tag, ptr) )
				return 0;
			bio_hdr->_present |= BIO_HDR_DATE;
			break;
		case TAG_BIO_HDR_VALIDITY:
			if ( !autober_octet(bio_hdr->validity, &tag, ptr) )
				return 0;
			bio_hdr->_present |= BIO_HDR_VALIDITY;
			break;
		case TAG_BIO_HDR_CREATOR_PID:
			if ( !autober_octet(bio_hdr->creator_pid, &tag, ptr) )
				return 0;
			bio_hdr->_present |= BIO_HDR_CREATOR_PID;
			break;
		case TAG_BIO_HDR_FORMAT_OWNER:
			if ( !autober_octet(bio_hdr->format_owner, &tag, ptr) )
				return 0;
			break;
		case TAG_BIO_HDR_FORMAT_TYPE:
			if ( !autober_octet(bio_hdr->format_type, &tag, ptr) )
				return 0;
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

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_INF_BIO_HDR:
			if ( !_bio_hdr(&bio_inf->bio_hdr, ptr, tag.ber_len) )
				return 0;
			break;
		case TAG_BIO_INF_BDB_NC:
			if ( !autober_blob(&bio_inf->bdb.bdb_nc, &tag, ptr) )
				return 0;
			bio_inf->_bdb_type = BIO_INF_BDB_TYPE_BDB_NC;
			break;
		case TAG_BIO_INF_BDB_C:
			if ( !autober_blob(&bio_inf->bdb.bdb_c, &tag, ptr) )
				return 0;
			bio_inf->_bdb_type = BIO_INF_BDB_TYPE_BDB_C;
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return 0;
		}
	}

	if ( !bio_inf->_bdb_type ) {
		fprintf(stderr, "bio_inf.bdb: at least one union "
				"member must be present\n");
		return 0;
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

	bio_group->bio_inf = calloc(cons[1].count, sizeof(*bio_group->bio_inf));
	if ( NULL == bio_group->bio_inf )
		return 0;

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_GROUP_NUM_INSTANCES:
			if ( !autober_u8(&bio_group->num_instances, &tag, ptr) )
				return 0;
			break;
		case TAG_BIO_GROUP_BIO_INF:
			if ( !_bio_inf(&bio_group->bio_inf[bio_group->_bio_inf_count], ptr, tag.ber_len) )
				return 0;
			bio_group->_bio_inf_count++;
			break;
		default:
			fprintf(stderr, "Unexpected tag\n");
			return 0;
		}
	}

	return 1;
}

static int _root(struct bio_group *bio_group,
				const uint8_t *ptr, size_t len)
{
	static const unsigned int num = AUTOBER_NUM_TAGS(root_tags);
	struct autober_constraint cons[num];
	struct gber_tag tag;
	const uint8_t *end;

	if ( !autober_constraints(root_tags, cons, num, ptr, len) ) {
		fprintf(stderr, "root_tags: constraints not satisified\n");
		return 0;
	}

	for(end = ptr + len; ptr < end; ptr += tag.ber_len) {
		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		if ( NULL == ptr )
			return 0;

		switch(tag.ber_tag) {
		case TAG_BIO_GROUP:
			if ( !_bio_group(bio_group, ptr, tag.ber_len) )
				return 0;
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
	struct bio_group *bio_group;

	bio_group = calloc(1, sizeof(*bio_group));
	if ( NULL == bio_group )
		return NULL;

	if ( !_root(bio_group, ptr, len) ) {
		_free_bio_group(bio_group);
		return NULL;
	}

	return bio_group;
}
