#include <stdlib.h>
#include <stdint.h>
#include "gber.h"

const char * const ber_id_octet_clsname(uint8_t id)
{
	static const char * const clsname[]={
		"universal",
		"application",
		"context-specific",
		"private",
	};
	return clsname[(id & 0xc0) >> 6];
}

unsigned int ber_id_octet_class(uint8_t id)
{
	return (id & 0xc0) >> 6;
}

unsigned int ber_id_octet_constructed(uint8_t id)
{
	return (id & 0x20) >> 5;
}

static uint8_t ber_len_form_short(uint8_t lb)
{
	return !(lb & 0x80);
}

static uint8_t ber_len_short(uint8_t lb)
{
	return lb & ~0x80;
}

const uint8_t *ber_decode_tag(struct gber_tag *tag,
				const uint8_t *ptr, size_t len)
{
	const uint8_t *end = ptr + len;

	if ( len < 2 )
		return NULL;

	tag->ber_id = *(ptr++);
	tag->ber_tag = tag->ber_id;
	if ( (tag->ber_id & 0x1f) == 0x1f ) {
		if ( (*ptr & 0x80) )
			return NULL;
		tag->ber_tag <<= 8;
		tag->ber_tag |= *(ptr++);
		if ( ptr >= end )
			return NULL;
	}

	if ( ber_len_form_short(*ptr) ) {
		tag->ber_len = ber_len_short(*ptr);
		ptr++;
	}else{
		unsigned int i;
		uint8_t ll;

		ll = ber_len_short(*(ptr++));
		if ( ptr + ll > end || ll > 4 )
			return NULL;

		for(tag->ber_len = 0, i = 0; i < ll; i++, ptr++) {
			tag->ber_len <<= 8;
			tag->ber_len |= *ptr;
		}
	}

	if ( ptr + tag->ber_len > end )
		return NULL;

	return ptr;
}
