class Root:
	def __init__(self):
		self.children = []
	def add(self, child):
		self.children.append(child)
	def __iter__(self):
		return self.children.__iter__()
	def __len__(self):
		return len(self.children)
	def pretty_print(self, root = None, depth = 0):
		if not root:
			root = self
		for x in root:
			print "%s%s"%(''.join("  " for x in range(depth)), x)
			if x.__class__ != Fixed:
				self.pretty_print(x, depth + 1)


class Template(Root):
	def __init__(self, tag, name, label):
		self.tag = tag
		self.name = name
		self.label = label
		Root.__init__(self)
	def __str__(self):
		return "T(%s)"%self.label
	def __repr__(self):
		return "Template(0x%x, '%s', '%s')"%(self.tag,
							self.name,
							self.label)

class Union(Root):
	def __init__(self, name, label):
		self.name = name
		self.label = label
		Root.__init__(self)
	def __str__(self):
		return "U(%s)"%self.label
	def __repr__(self):
		return "Union('%s', '%s')"%(self.name, self.label)

class Fixed:
	def __init__(self, tag, type, name):
		self.tag = tag
		self.type = type
		self.name = name
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
	STATE_T_LABEL	= 3 # template label
	STATE_F_TYPE	= 4 # fixed type
	STATE_F_NAME	= 5 # fixed name
	STATE_PUSH	= 6 # recurse
	STATE_POP	= 7 # recurse
	STATE_ADD	= 8 # add fixed item

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
		if tok == '}':
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

		if tok == 'union':
			self.__union = True
			self.__state = self.STATE_T_NAME
		else:
			self.__tagno = int(tok, 0)
			assert(self.__tagno < 0x10000)
			self.__state = self.STATE_FLAGS
		return True

	def __flags(self, tok):
		if tok == "OPTIONAL":
			self.__optional = True
			return True
		if tok == "NOCONSTRUCT":
			self.__noconstruct = True
			return True
		if self.__template():
			self.__state = self.STATE_T_NAME
		else:
			self.__state = self.STATE_F_TYPE
		return False

	def __t_name(self, tok):
		self.__name = tok
		self.__state = self.STATE_T_LABEL
		return True

	def __t_label(self, tok):
		self.__label = tok
		self.__state = self.STATE_PUSH
		return True

	def __f_type(self, tok):
		self.__type = tok
		self.__state = self.STATE_F_NAME
		return True

	def __f_name(self, tok):
		self.__name = tok
		self.__state = self.STATE_ADD
		return True

	def __f_push(self, tok):
		assert(tok == '{')
		assert(self.__template())

		if self.__union:
			tmpl = Union(self.__name, self.__label)
		else:
			tmpl = Template(self.__tagno, self.__name, self.__label)
		x = self.__stack.pop()
		x.add(tmpl)
		self.__stack.append(x)
		self.__stack.append(tmpl)
		self.__state = self.STATE_TAG
		return True
	
	def __f_pop(self, tok):
		assert(tok == '}')
		self.__state = self.STATE_TAG
		self.__stack.pop()
		return True
	
	def __f_add(self, tok):
		assert(tok == ';')
		fixd = Fixed(self.__tagno, self.__type, self.__name)
		x = self.__stack.pop()
		x.add(fixd)
		self.__stack.append(x)
		self.__state = self.STATE_TAG
		return True

	def __parse(self):
		transitions = {
			self.STATE_TAG: self.__tag,
			self.STATE_FLAGS: self.__flags,
			self.STATE_T_NAME: self.__t_name,
			self.STATE_T_LABEL: self.__t_label,
			self.STATE_F_TYPE: self.__f_type,
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
