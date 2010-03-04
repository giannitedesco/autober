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
	NONE		= 0
	OPTIONAL 	= 1
	NOCONSTRUCT	= 2
	UNION		= 3
	def __getitem__(self, idx):
		return self.__map.get(idx, self.NONE)
	def __init__(self, tok):
		self.__map = {"OPTIONAL": self.OPTIONAL,
				"NOCONSTRUCT": self.NOCONSTRUCT,
				"union": self.UNION}
		self.__rmap = {self.OPTIONAL: "OPTIONAL",
				self.NOCONSTRUCT: "NOCONSTRUCT",
				self.UNION: "union"}
		self.keyword = self[tok]
	def __str__(self):
		return self.__rmap.get(self.keyword, "NONE")
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
		return "'%s'"%self.__string
	def __repr__(self):
		return "%s"%self.__string

class LexOpenBrace(LexToken):
	def __str__(self):
		return "{"

class LexCloseBrace(LexToken):
	def __str__(self):
		return "}"

class LexSemiColon(LexToken):
	def __str__(self):
		return ";"

class lexer:
	def __top(self):
		if not len(self.__toks):
			return None
		[ret] = self.__toks[-1:]
		return ret

	def __paste(self, tok):
		x = self.__toks.pop()
		self.__toks.append(x[:-1] + tok)

	def __append(self, tok):
		self.__toks.append(tok)

	def __extend(self, list):
		for tok in list:
			self.__append(tok)

	def __strip_comments(self, ss):
		res = []
		inc = False
		for s in ss:
			if not inc and s == '/*':
				inc = True
				continue
			if inc and s == '*/':
				inc = False
				continue
			if not inc:
				res.append(s)
		return res

	def __paste_strings(self, ss):
		res = []
		instr = False
		str = ''
		for s in ss:
			if not instr and s == "'":
				instr = True
				str = ''
				continue
			if instr:
				if s == '\n':
					continue
				if s == "'":
					if str[-1:] == '\\':
						str = str[:-1] + s
						continue
					else:
						res.append(LexString(str))
						instr = False
						continue
				else:
					str = str + s
			else:
				res.append(s)
		return res

	def __strip_whitespace(self, ss):
		return filter(lambda x:not (x.isspace() or x == ''), ss)

	def __split(self, str):
		res = []
		inw = False
		tok = ''
		for c in str:
			if not inw and c.isspace():
				if len(tok):
					res.append(tok)
				tok = c
				inw = True
				continue
			if inw and not c.isspace():
				res.append(tok)
				tok = c
				inw = False
				continue
			tok = tok + c
		if len(tok):
			res.append(tok)
		return res

	def __split_on(self, ss, char):
		res = []
		for str in ss:
			if LexToken in str.__class__.__bases__:
				res.append(str)
				continue
			while len(str):
				(tok, s, rest) = str.partition(char)
				if not tok == '':
					res.append(tok)
				if s == char:
					res.append(s)
				str = rest

		return res

	def __tag_one(self, tok):
		if LexToken in tok.__class__.__bases__:
			return tok
		kw = LexKeyword(tok)
		if kw.keyword != kw.NONE:
			return kw
		if tok == '{':
			return LexOpenBrace()
		if tok == '}':
			return LexCloseBrace()
		if tok == ';':
			return LexSemiColon()
		if tok[0].isalpha():
			return LexIdentifier(tok)
		if tok[0].isdigit():
			r = tok.split("-", 1)
			if len(r) == 1:
				return LexInteger(r[0])
			else:
				return LexIntRange(r[0], r[1])
		print "UNTAGGED: %s"%tok
		return tok

	def __tag_all(self, tok_stream):
		res = []
		insub = False
		ss = None
		for tok in tok_stream:
			if insub:
				if tok == ']':
					insub = False
					res.append(ss)
				else:
					ss.set_subscript(self.__tag_one(tok))
				continue
			if not insub and tok == '[':
				insub = True
				ss = LexSubscript()
				continue
			ltok = self.__tag_one(tok)
			res.append(ltok)
		return res

	def __tokenize(self, str):
		ss = []
		while len(str):
			(tok, s, rest) = str.partition("'")
			ss.extend(self.__split(tok))
			if s == "'":
				ss.extend(s)
			str = rest
		ss = self.__strip_comments(ss)
		ss = self.__paste_strings(ss)
		ss = self.__strip_whitespace(ss)
		ss = self.__split_on(ss, ';')
		ss = self.__split_on(ss, '{')
		ss = self.__split_on(ss, '}')
		ss = self.__split_on(ss, '[')
		ss = self.__split_on(ss, ']')
		ss = self.__tag_all(ss)
		self.__extend(ss)

	def __iter__(self):
		return self.__toks.__iter__()

	def __init__(self, file):
		lines = file.readlines()
		lines = map(lambda x:x.rstrip('\r\n'), lines)
		self.__toks = []
		self.__tokenize("\n".join(lines))
		return
