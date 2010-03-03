/*
 * This file is part of autober
 * Copyright (c) 2010 Gianni Tedesco <gianni@scaramanga.co.uk>
 * Released under the terms of the GNU GPL version 3
*/

#ifndef _AUTOBER_H
#define _AUTOBER_H

struct autober_blob {
	uint8_t *ptr;
	size_t len;
};

#define AUTOBER_TYPE_BLOB	0
#define AUTOBER_TYPE_OCTET	1
#define AUTOBER_TYPE_INT	2 /* min = octets */
#define AUTOBER_TYPE_BCD	3 /* min elements of max binary digits */
typedef unsigned int autober_type_t;

#define AUTOBER_TEMPLATE	(1<<0)
#define AUTOBER_UNION		(1<<1) /* only valid for templates */
#define AUTOBER_SEQUENCE	(1<<2) /* only valid for templates */
#define AUTOBER_OPTIONAL	(1<<3)
#define AUTOBER_CHECK_SIZE	(1<<4) /* semantics type specific */
struct autober_tag {
	gber_tag_t	ab_tag;
	unsigned int	ab_flags;
	size_t		ab_count[2];
	autober_type_t	ab_type;
	const char	*ab_label;
};

struct autober_constraint {
	unsigned int count;
	size_t len; /* for fixed fields only */
};

#define AUTOBER_NUM_TAGS(tags) (sizeof(tags)/sizeof(*tags))
const struct autober_tag *find_tag(const struct autober_tag *tags,
					unsigned int n, gber_tag_t id);
int autober_constraints(const struct autober_tag *tags,
				struct autober_constraint *cons,
				unsigned int num_tags,
				const uint8_t *ptr, size_t len);

#endif /* _AUTOBER_H */