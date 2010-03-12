from tokens import *

class Root:
	def __init__(self):
		self.children = []
		self.parent = None
		self.name = ''
		self.optional = False
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
	def __init__(self, tag, name, subscript, label, optional = False):
		Root.__init__(self)
		self.tag = tag
		self.name = name
		self.label = label
		self.cur_opt = 0
		self.optional = optional
		self.optindex = -1
		if subscript == None:
			self.sequence = False
		else:
			if subscript.get_subscript() == None:
				self.sequence = True
			else:
				raise Exception("Template arrays not supported")
	def __str__(self):
		return "Template(%s)"%self.label
	def __repr__(self):
		return "Template(0x%x, '%s', %s)"%(self.tag,
							self.name,
					self.label.replace('\'', '\\\''))

class Union(Root):
	def __init__(self, name, label):
		Root.__init__(self)
		self.name = name
		self.label = label
		self.cur_opt = 0
	def __str__(self):
		return "Union(%s)"%self.label
	def __repr__(self):
		return "Union('%s', '%s')"%(self.name, self.label)

class Fixed:
	def __init__(self, tag, name, optional = False):
		self.tag = tag
		self.name = name
		self.optional = optional
		self.constraint = None
		self.bytes = 0
	def __iter__(self):
		return [].__iter__()
	def __str__(self):
		return "F(%s)"%self.name
	def __repr__(self):
		return "Fixed(0x%x, '%s')"%(self.tag, self.name)

class Uint(Fixed):
	BITS_PER_BYTE		= 8

	def __init__(self, tag, bits, name, optional = False):
		Fixed.__init__(self, tag, name, optional)
		assert((bits % self.BITS_PER_BYTE) == 0)
		self.bits = bits
		self.bytes = bits / self.BITS_PER_BYTE
		self.constraint = (self.bytes, self.bytes)
	def set_subscript(self, ss):
		if ss.__class__ == LexInteger:
			min = max = int(ss)
		elif ss.__class__ == LexIntRange:
			(min, max) = ss 
		else:
			raise Exception("WTF %s"%ss)
		self.constraint = (min * self.bytes, max * self.bytes)
	def __str__(self):
		if (1, 1) == self.constraint:
			return "Uint%u(%s)"%(self.bits, self.name)
		elif self.constraint[0] == self.constraint[1]:
			return "Uint%u[%u](%s)"%(self.bits,
							self.constraint[0],
							self.name)
		else:
			return "Uint%u[%u:%u](%s)"%(self.bits,
							self.constraint[0],
							self.constraint[1],
							self.name)


class Uint8(Uint,Fixed):
	def __init__(self, tag, name, optional = False):
		Uint.__init__(self, tag, 8, name, optional)
class Octet(Uint,Fixed):
	def __init__(self, tag, name, optional = False):
		Uint.__init__(self, tag, 8, name, optional)
	def __str__(self):
		if (1, 1) == self.constraint:
			return "Octet(%s)"%(self.name)
		elif self.constraint[0] == self.constraint[1]:
			return "Octet[%u](%s)"%(self.constraint[0],
						self.name)
		else:
			return "Octet[%u:%u](%s)"%(self.constraint[0],
							self.constraint[1],
							self.name)
class Uint16(Uint,Fixed):
	def __init__(self, tag, name, optional = False):
		Uint.__init__(self, tag, 16, name, optional)
class Uint32(Uint,Fixed):
	def __init__(self, tag, name, optional = False):
		Uint.__init__(self, tag, 32, name, optional)
class Uint64(Uint,Fixed):
	def __init__(self, tag, name, optional = False):
		Uint.__init__(self, tag, 64, name, optional)

class Blob(Fixed):
	def __init__(self, tag, name, optional = False):
		Fixed.__init__(self, tag, name, optional)
	def __str__(self):
		return "Blob(%s)"%self.name
