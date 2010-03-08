/* Biometric data from EF.DG2 file in ICAO9303 compliant e-passport */
0x7f61 bio_group 'Biometric Information Group Template' {
	0x2 uint8_t num_instances;
	0x7f60 bio_inf[] 'Biometric \'Information\' Template' {
		0xa1 bio_hdr 'Biometric Header Template' {
			0x80 uint16_t vers;
			0x81 OPTIONAL octet[1-3] type;
			0x82 OPTIONAL uint8_t subtype;
			0x83 OPTIONAL octet[7] date;
			0x85 OPTIONAL octet[8] validity;
			0x86 OPTIONAL octet[2] creator_pid;
			0x87 octet[2] format_owner;
			0x88 octet[2] format_type;
		}
		union bdb 'Biometric Data Block' {
			0x5f2e blob bdb_nc;
			0x7f2e NOCONSTRUCT blob bdb_c;
		}
	}
}
