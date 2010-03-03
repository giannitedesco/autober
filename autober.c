#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <gber.h>
#include <autober.h>

static const struct autober_tag *do_find_tag(const struct autober_tag *tags,
					unsigned int n, gber_tag_t id)
{
	const struct autober_tag *t;

	for(t = tags; n; ) {
		unsigned int i;
		int cmp;

		i = n / 2U;
		cmp = id - t[i].ab_tag;
		if ( cmp < 0 ) {
			n = i;
		}else if ( cmp > 0 ) {
			t = t + (i + 1U);
			n = n - (i + 1U);
		}else
			return t + i;
	}

	return NULL;
}

const struct autober_tag *find_tag(const struct autober_tag *tags,
					unsigned int n, gber_tag_t id)
{
	return do_find_tag(tags, n, id);
}

int autober_constraints(const struct autober_tag *tags,
				struct autober_constraint *cons,
				unsigned int num_tags,
				const uint8_t *ptr, size_t len)
{
	const uint8_t *end = ptr + len;
	unsigned int i;

	memset(cons, 0, sizeof(*cons) * num_tags);

	while(ptr < end) {
		const struct autober_tag *atag;
		unsigned int idx;
		struct gber_tag tag;

		ptr = ber_decode_tag(&tag, ptr, end - ptr);
		atag = do_find_tag(tags, num_tags, tag.ber_tag);
		if ( NULL == atag ) {
			fprintf(stderr, "autober: tag 0x%x not found\n",
				tag.ber_tag);
			return 0;
		}

		idx = atag - tags;
		if ( atag->ab_flags & AUTOBER_TEMPLATE ) {
			if ( cons[idx].count && 
				!(atag->ab_flags & AUTOBER_SEQUENCE) ) {
				fprintf(stderr, "%s not expecting sequence\n",
					atag->ab_label);
				return 0;
			}
			cons[idx].count++;
			printf("field[%u] template: %s: count = %u\n",
				idx, atag->ab_label, cons[idx].count);
		}else{
			if ( cons[idx].count ) {
				fprintf(stderr, "%s multiply defined\n",
					atag->ab_label);
				return 0;
			}
			cons[idx].count++;
			cons[idx].len = tag.ber_len;
			printf("field[%u] fixed: %s: len = %u\n",
				idx, atag->ab_label, cons[idx].len);
		}

		ptr += tag.ber_len;
	}

	for(i = 0; i < num_tags; i++) {
		if ( (tags[i].ab_flags & (AUTOBER_OPTIONAL|AUTOBER_UNION))
			== AUTOBER_OPTIONAL && cons[i].count == 0 ) {
			fprintf(stderr, "Mandatory tag: %s: missing\n",
				tags[i].ab_label);
		}
	}

	return 1;
}
