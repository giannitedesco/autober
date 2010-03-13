/* EMV application file control */
0x6f adf_fci 'File Control Information' {
	0x84 octet[5-16] df_name;
	0xa5 adf 'FCI Proprietary Template' {
		0x50	OPTIONAL octet[1-16] 	label;
		0x87	OPTIONAL uint8_t 	prio;
		0x9f38	OPTIONAL octet[1-16]	pdol;
		0x5f2d	OPTIONAL octet[1-16]	language;
		0x9f11	OPTIONAL octet[1-16]	issuer_code;
		0x9f12  OPTIONAL octet[1-16]	pname;
		0xbf0c  OPTIONAL fci_idd 'FCI Issuer Discretionary Data' {
			0x9f4d OPTIONAL octet[1-16] log_entry;
		}
	}
}
