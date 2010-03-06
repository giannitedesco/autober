class LexToken:
	def isspace(self):
		return False

class LexInteger(LexToken):
	def __init__(self, str):
		self.integer = int(str, 0)
	def __str__(self):
		return "0x%x"%self.integer
	def __int__(self):
		return self.integer

class LexIntRange(LexToken):
	def __init__(self, strmin, strmax):
		self.min = int(strmin, 0)
		self.max = int(strmax, 0)
	def __str__(self):
		return "%u-%u"%(self.min, self.max)
	def __getitem__(self, idx):
		if idx == 0:
			return self.min
		elif idx == 1:
			return self.max
		else:
			raise IndexError

class LexKeyword(LexToken):
	OPTIONAL 	= 0
	NOCONSTRUCT	= 1
	UNION		= 2
	def __getitem__(self, idx):
		return self.__map[idx]
	def __init__(self, tok):
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
	def __init__(self, tok):
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
	def __init__(self, str):
		self.name = str
	def __str__(self):
		return self.name

class LexSubscript(LexToken):
	def __init__(self):
		self.__item = None
	def set_subscript(self, tok):
		if self.__item:
			raise Exception("Only one token per subscript")
		self.__item = tok
	def get_subscript(self):
		return self.__item
	def __str__(self):
		return "[%s]"%self.__item

class LexString(LexToken):
	def __init__(self, str):
		self.__string = filter(lambda x:x != '\n', str)
	def __str__(self):
		return "%s"%self.__string
	def __repr__(self):
		return "'%s'"%self.__string.replace("'", "\\'")

class LexOpenBrace(LexToken):
	def __str__(self):
		return "{"

class LexCloseBrace(LexToken):
	def __str__(self):
		return "}"

class LexSemiColon(LexToken):
	def __str__(self):
		return ";"

