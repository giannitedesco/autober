/*
 * This file is part of autober
 * Copyright (c) 2010 Gianni Tedesco <gianni@scaramanga.co.uk>
 * Released under the terms of the GNU GPL version 3
*/

#ifndef _BIO_GROUP_H
#define _BIO_GROUP_H

#define TAG_BIO_GROUP				0x7f61
#define TAG_BIO_GROUP_NUM_INSTANCES		0x02
#define TAG_BIO_GROUP_BIO_INF			0x7f60
#define TAG_BIO_INF_BIO_HDR			0xa1
#define TAG_BIO_INF_BDB_NC			0x5f2e
#define TAG_BIO_INF_BDB_C			0x7f2e
#define TAG_BIO_HDR_VERS			0x80
#define TAG_BIO_HDR_TYPE			0x81
#define TAG_BIO_HDR_SUBTYPE			0x82
#define TAG_BIO_HDR_DATE			0x83
#define TAG_BIO_HDR_VALIDITY			0x85
#define TAG_BIO_HDR_CREATOR_PID			0x86
#define TAG_BIO_HDR_FORMAT_OWNER		0x87
#define TAG_BIO_HDR_FORMAT_TYPE			0x88

#define BIO_HDR_TYPE				(1<<0)
#define BIO_HDR_SUBTYPE				(1<<1)
#define BIO_HDR_DATE				(1<<2)
#define BIO_HDR_VALIDITY			(1<<3)
#define BIO_HDR_CREATOR_PID			(1<<4)

#define BIO_INF_BDB_TYPE_BDB_NC			1
#define BIO_INF_BDB_TYPE_BDB_C			2

struct bio_group {
	uint8_t num_instances;
	struct bio_inf *bio_inf;
	unsigned int _bio_inf_count;
};

struct bio_inf {
	struct bio_hdr {
		uint16_t vers;
		uint8_t type[3];
		size_t _type_len;
		uint8_t subtype;
		uint8_t date[7];
		uint8_t validity[8];
		uint8_t creator_pid[2];
		uint8_t format_owner[2];
		uint8_t format_type[2];
		unsigned long int _present;
	}bio_hdr;
	unsigned int _bdb_type;
	union {
		struct autober_blob bdb_nc;
		struct autober_blob bdb_c;
	}bdb;
};

struct bio_group *bio_group_decode(const uint8_t *ptr, size_t len);
void bio_group_free(struct bio_group *bio_group);

#endif /* _BIO_GROUP_H */
