from lexer import LexToken, LexInteger, LexIntRange, LexKeyword, LexType
from lexer import LexIdentifier, LexSubscript, LexString 
from lexer import LexOpenBrace, LexCloseBrace, LexSemiColon

class Root:
	def __init__(self):
		self.children = []
		self.parent = None
		self.name = ''
	def add(self, child):
		self.children.append(child)
	def __iter__(self):
		return self.children.__iter__()
	def __getitem__(self, idx):
		return self.children[idx]
	def __len__(self):
		return len(self.children)
	def pretty_print(self, root = None, depth = 0):
		if not root:
			root = self
		for x in root:
			print "%s%s"%(''.join("  " for x in range(depth)), x)
			self.pretty_print(x, depth + 1)


class Template(Root):
	def __init__(self, tag, name, subscript, label):
		Root.__init__(self)
		self.tag = tag
		self.name = name
		self.label = label
		self.optindex = 0
		if subscript == None:
			self.sequence = False
		else:
			if subscript.get_subscript() == None:
				self.sequence = True
			else:
				raise Exception("Template arrays not supported")
	def __str__(self):
		return "T(%s)"%self.label
	def __repr__(self):
		return "Template(0x%x, '%s', %s)"%(self.tag,
							self.name,
					self.label.replace('\'', '\\\''))

class Union(Root):
	def __init__(self, name, label):
		Root.__init__(self)
		self.name = name
		self.label = label
		self.optindex = 0
	def __str__(self):
		return "U(%s)"%self.label
	def __repr__(self):
		return "Union('%s', '%s')"%(self.name, self.label)

class Fixed:
	def __init__(self, tag, type, subscript, name, optional = False):
		self.tag = tag
		self.type = type
		self.name = name
		self.optional = optional
		if subscript:
			ss = subscript.get_subscript()
			if ss.__class__ == LexInteger:
				min = max = int(ss)
			elif ss.__class__ == LexIntRange:
				(min, max) = ss 
			else:
				raise Exception("WTF %s"%ss)
			self.constraint = (min, max)
		else:
			self.constraint = None
	def __iter__(self):
		return [].__iter__()
	def __str__(self):
		return "F(%s)"%self.name
	def __repr__(self):
		return "Fixed(0x%x, '%s', '%s')"%(self.tag,
							self.type,
							self.name)
class parser:
	STATE_TAG	= 0 # initial state
	STATE_FLAGS	= 1 # template/fixed flags
	STATE_T_NAME	= 2 # template name
	STATE_T_SUB	= 3 # template name
	STATE_T_LABEL	= 4 # template label
	STATE_F_TYPE	= 5 # fixed type
	STATE_F_SUB	= 6
	STATE_F_NAME	= 7 # fixed name
	STATE_PUSH	= 8 # recurse
	STATE_POP	= 9 # recurse
	STATE_ADD	= 10 # add fixed item

	def __template(self):
		if self.__noconstruct:
			return False
		if self.__union:
			return True
		if self.__tagno > 0xff:
			id = (self.__tagno >> 8)
		else:
			id = self.__tagno
		assert ((id & 0xff) == id)
		return bool(id & 0x20)

	def __tag(self, tok):
		if tok.__class__ == LexCloseBrace:
			self.__state = self.STATE_POP
			return False

		# setup initial state
		self.__noconstruct = False
		self.__optional = False
		self.__union = False
		self.__tagno = 0
		self.__name = ''
		self.__label = None
		self.__type = None
		self.__subscript = None

		if tok.__class__ == LexInteger:
			self.__tagno = int(tok)
			if self.__tagno > 0xffff:
				raise Exception("Parse error")
			self.__state = self.STATE_FLAGS
			return True
		elif tok.__class__ == LexKeyword:
			if int(tok) == tok.UNION:
				self.__union = True
				self.__state = self.STATE_T_NAME
				return True
		raise Exception("Parse error")

	def __flags(self, tok):
		if tok.__class__ == LexKeyword:
			if int(tok) == tok.OPTIONAL:
				self.__optional = True
				return True
			if int(tok) == tok.NOCONSTRUCT:
				self.__noconstruct = True
				return True
			raise Exception("Parse error")
		if self.__template():
			self.__state = self.STATE_T_NAME
		else:
			self.__state = self.STATE_F_TYPE
		return False

	def __t_name(self, tok):
		if tok.__class__ != LexIdentifier:
			raise Exception("Parse error")
		self.__name = str(tok)
		self.__state = self.STATE_T_SUB
		return True

	def __t_sub(self, tok):
		if tok.__class__ != LexSubscript:
			self.__state = self.STATE_T_LABEL
			return False
		self.__subscript = tok
		self.__state = self.STATE_T_LABEL
		return True

	def __t_label(self, tok):
		if tok.__class__ != LexString:
			raise Exception("Parse error")
		self.__label = str(tok)
		self.__state = self.STATE_PUSH
		return True

	def __f_type(self, tok):
		if tok.__class__ != LexType:
			raise Exception("Parse error")
		self.__type = tok
		self.__state = self.STATE_F_SUB
		return True

	def __f_sub(self, tok):
		if tok.__class__ != LexSubscript:
			self.__state = self.STATE_F_NAME
			return False
		self.__subscript = tok
		self.__state = self.STATE_F_NAME
		return True

	def __f_name(self, tok):
		if tok.__class__ != LexIdentifier:
			raise Exception("Parse error")
		self.__name = str(tok)
		self.__state = self.STATE_ADD
		return True

	def __f_push(self, tok):
		if not self.__template():
			raise Exception("Parse Error:")

		if tok.__class__ != LexOpenBrace:
			raise Exception("Parse Error:")

		if self.__union:
			tmpl = Union(self.__name, self.__label)
		else:
			tmpl = Template(self.__tagno, self.__name,
					self.__subscript, self.__label)
		x = self.__stack.pop()
		tmpl.parent = x
		x.add(tmpl)
		self.__stack.append(x)
		self.__stack.append(tmpl)
		self.__state = self.STATE_TAG
		return True
	
	def __f_pop(self, tok):
		if tok.__class__ != LexCloseBrace:
			raise Exception("Parse Error")
		self.__state = self.STATE_TAG
		self.__stack.pop()
		return True
	
	def __f_add(self, tok):
		if tok.__class__ != LexSemiColon:
			raise Exception("Parse Error: %s")
		fixd = Fixed(self.__tagno, self.__type,
				self.__subscript, self.__name,
				self.__optional)
		x = self.__stack.pop()
		fixd.parent = x
		if self.__optional or x.__class__ == Union:
			fixd.optindex = x.optindex
			x.optindex += 1
		x.add(fixd)
		self.__stack.append(x)
		self.__state = self.STATE_TAG
		return True

	def __parse(self):
		transitions = {
			self.STATE_TAG: self.__tag,
			self.STATE_FLAGS: self.__flags,
			self.STATE_T_NAME: self.__t_name,
			self.STATE_T_SUB: self.__t_sub,
			self.STATE_T_LABEL: self.__t_label,
			self.STATE_F_TYPE: self.__f_type,
			self.STATE_F_SUB: self.__f_sub,
			self.STATE_F_NAME: self.__f_name,
			self.STATE_PUSH: self.__f_push,
			self.STATE_POP: self.__f_pop,
			self.STATE_ADD: self.__f_add,
		}

		for tok in self.__iter:
			#print "Input token: %s"%tok
			while not transitions[self.__state](tok):
				continue

	def __init__(self, lex):
		self.__state = self.STATE_TAG
		self.__iter = lex.__iter__()
		self.__stack = [Root()]
		self.__parse()
		r = self.__stack.pop()
		assert(len(r) == 1)
		self.__parse_tree = r
	
	def parse_tree(self):
		return self.__parse_tree
