class LexToken:
	def __init__(self, filename, lineno):
		self.filename = filename
		self.lineno = lineno
	def __repr__(self):
		return "%s(%s)"%(self.__class__.__name__, str(self))

class LexInteger(LexToken):
	def __init__(self, filename, lineno, str):
		LexToken.__init__(self, filename, lineno)
		self.strform = str
		self.integer = int(str, 0)
	def __str__(self):
		# for nicer error messages
		return "%s"%self.strform
	def __int__(self):
		return self.integer

class LexKeyword(LexToken):
	OPTIONAL 	= 0
	NOCONSTRUCT	= 1
	UNION		= 2
	def __getitem__(self, idx):
		return self.__map[idx]
	def __init__(self, filename, lineno, tok):
		LexToken.__init__(self, filename, lineno)
		self.__map = {"OPTIONAL": self.OPTIONAL,
				"NOCONSTRUCT": self.NOCONSTRUCT,
				"union": self.UNION}
		self.__rmap = {self.OPTIONAL: "OPTIONAL",
				self.NOCONSTRUCT: "NOCONSTRUCT",
				self.UNION: "union"}
		self.keyword = self[tok]
	def __str__(self):
		return self.__rmap[self.keyword]
	def __int__(self):
		return self.keyword

class LexType(LexToken):
	OCTET		= 0
	UINT8		= 1
	UINT16		= 2
	UINT32		= 3
	UINT64		= 4
	BLOB		= 5
	def __getitem__(self, idx):
		return self.__map[idx]
	def __init__(self, filename, lineno, tok):
		LexToken.__init__(self, filename, lineno)
		self.__map = {"octet": self.OCTET,
				"uint8_t": self.UINT8,
				"uint16_t": self.UINT16,
				"uint32_t": self.UINT32,
				"uint64_t": self.UINT64,
				"blob": self.BLOB}
		self.__rmap = {self.OCTET: "octet",
				self.UINT8: "uint8_t",
				self.UINT16: "uint16_t",
				self.UINT32: "uint32_t",
				self.UINT64: "uint64_t",
				self.BLOB: "blob"}
		self.type_id = self[tok]
	def __str__(self):
		return self.__rmap[self.type_id]
	def __int__(self):
		return self.keyword

class LexIdentifier(LexToken):
	def __init__(self, filename, lineno, str):
		LexToken.__init__(self, filename, lineno)
		self.name = str
	def __str__(self):
		return self.name

class LexString(LexToken):
	def __init__(self, filename, lineno, str):
		LexToken.__init__(self, filename, lineno)
		self.__string = filter(lambda x:x != '\n', str)
	def __str__(self):
		return "%s"%self.__string

class LexOpenBrace(LexToken):
	def __str__(self):
		return "{"

class LexCloseBrace(LexToken):
	def __str__(self):
		return "}"

class LexOpenSub(LexToken):
	def __str__(self):
		return "["

class LexCloseSub(LexToken):
	def __str__(self):
		return "]"

class LexSemiColon(LexToken):
	def __str__(self):
		return ";"

class LexRange(LexToken):
	def __str__(self):
		return "-"
