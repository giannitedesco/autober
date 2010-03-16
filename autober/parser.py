from errors import *
from tokens import *
from syntax import *

class parser:
	STATE_TAG	= 0 # initial state
	STATE_FLAGS	= 1 # template/fixed flags
	STATE_T_NAME	= 2 # template name
	STATE_T_SUB	= 3 # template subscript
	STATE_T_LABEL	= 4 # template label
	STATE_F_TYPE	= 5 # fixed type
	STATE_F_SUB	= 6 # fixed subscript
	STATE_F_NAME	= 7 # fixed name
	STATE_PUSH	= 8 # recurse
	STATE_POP	= 9 # recurse
	STATE_ADD	= 10 # add fixed item

	__types 	= {"octet": Octet,
				"uint8_t": Uint8,
				"uint16_t": Uint16,
				"uint32_t": Uint32,
				"uint64_t": Uint64,
				"blob": Blob,
			}

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
		self.__subtokens = None
		self.__sequence = None

		if tok.__class__ == LexInteger:
			self.__tagno = int(tok)
			assert(self.__tagno >= 0)
			if self.__tagno > 0xffff:
				raise BadSyntax(tok, "Bad tag number")
			self.__state = self.STATE_FLAGS
			return True
		elif tok.__class__ == LexKeyword:
			if int(tok) == tok.UNION:
				self.__union = True
				self.__state = self.STATE_T_NAME
				return True
		raise BadSyntax(tok, "Expected union or template")

	def __flags(self, tok):
		if tok.__class__ == LexKeyword:
			if int(tok) == tok.OPTIONAL:
				self.__optional = True
				return True
			if int(tok) == tok.NOCONSTRUCT:
				self.__noconstruct = True
				return True
			raise BadSyntax(tok, "Unexpected keyword")
		if self.__template():
			self.__state = self.STATE_T_NAME
		else:
			self.__state = self.STATE_F_TYPE
		return False

	def __t_name(self, tok):
		if tok.__class__ != LexIdentifier:
			raise BadSyntax(tok, "Expected template identifier")
		self.__name = str(tok)
		self.__state = self.STATE_T_SUB
		return True

	def __t_sub(self, tok):
		if self.__sequence == None:
			if tok.__class__ != LexOpenSub:
				self.__state = self.STATE_T_LABEL
				self.__sequence = False
				return False
			else:
				self.__sequence = True
				return True
		if tok.__class__ == LexCloseSub:
			self.__state = self.STATE_T_LABEL
		else:
			# TODO: Template arrays
			raise BadSyntax(tok,
					"Template arrays not yet implemented")
		return True

	def __t_label(self, tok):
		if tok.__class__ != LexString:
			raise BadSyntax(tok, "Expected template label")
		self.__label = str(tok)
		self.__state = self.STATE_PUSH
		return True

	def __f_type(self, tok):
		if tok.__class__ != LexType:
			raise BadSyntax(tok, "Type must be one of: " + \
					', '.join(self.__types.keys()))
		self.__type = tok
		self.__state = self.STATE_F_SUB
		return True

	def __f_sub(self, tok):
		if self.__subtokens == None:
			if tok.__class__ != LexOpenSub:
				self.__state = self.STATE_F_NAME
				return False
			else:
				self.__subtokens = []
				return True
		if tok.__class__ == LexCloseSub:
			self.__state = self.STATE_F_NAME
		else:
			self.__subtokens.append(tok)
		return True

	def __f_name(self, tok):
		if tok.__class__ != LexIdentifier:
			raise BadSyntax(tok, "Expected fixed item identifier")
		self.__name = str(tok)
		self.__state = self.STATE_ADD
		return True

	def __f_push(self, tok):
		if not self.__template():
			raise BadSyntax(tok, "Tag 0x%x is not a template"%\
					self.__tagno)
					# "sugest: CONSTRUCT option"

		if tok.__class__ != LexOpenBrace:
			if self.__union:
				raise BadSyntax(tok, "Union element, "
						"expecting open brace")
			else:
				raise BadSyntax(tok,
					"Tag 0x%x is a template: "%\
					self.__tagno + "expecting open brace")

		if self.__union:
			tmpl = Union(self.__name, self.__label)
		else:
			tmpl = Template(self.__tagno, self.__name,
					self.__sequence, self.__label,
					self.__optional)
		x = self.__stack.pop()
		if self.__optional and not self.__union:
			tmpl.optindex = x.cur_opt
			x.cur_opt += 1
		tmpl.parent = x
		x.add(tmpl)
		self.__stack.append(x)
		self.__stack.append(tmpl)
		self.__state = self.STATE_TAG
		return True
	
	def __f_pop(self, tok):
		assert(tok.__class__ == LexCloseBrace)
		self.__state = self.STATE_TAG
		self.__stack.pop()
		return True
	
	def __f_add(self, tok):
		if tok.__class__ != LexSemiColon:
			raise BadSyntax(tok, "Missing semi-colon")

		try:
			cls = self.__types[str(self.__type)]
		except KeyError:
			raise BadSyntax(tok, "type must be one of: "%\
					', '.join(self.__types.keys()))

		fixd = cls(self.__tagno, self.__name,
				self.__subtokens, self.__optional)

		x = self.__stack.pop()
		fixd.parent = x
		if self.__optional or x.__class__ == Union:
			fixd.optindex = x.cur_opt
			x.cur_opt += 1
		x.add(fixd)
		self.__stack.append(x)
		self.__state = self.STATE_TAG
		return True

	def __init__(self, lex):
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

		self.__state = self.STATE_TAG
		self.__stack = [Root()]

		for tok in lex:
			#print "Input token: %s"%tok
			while not transitions[self.__state](tok):
				continue

		r = self.__stack.pop()
		assert(len(r) == 1)
		self.__parse_tree = r
	
	def parse_tree(self):
		return self.__parse_tree
