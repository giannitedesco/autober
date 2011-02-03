/* EMV paument system directory entry */
0x70 pse_fci 'Paymsent System Entry' {
	0x61 pse_app 'Payment System Entry' {
		0x4f	octet[5-16] pse_adf_name;
		0x50	octet[1-16] pse_label;
		0x9f12	OPTIONAL octet[1-16] pse_pname;
		0x87	uint8_t pse_prio;
	}
}
