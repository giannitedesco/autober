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
	def __init__(self, tag, name, sequence, label, optional = False):
		Root.__init__(self)
		self.tag = tag
		self.name = name
		self.label = label
		self.cur_opt = 0
		self.optional = optional
		self.optindex = -1
		self.sequence = sequence
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
	def add(self, child):
		if child.__class__ == Template and child.sequence:
			raise Exception("No template sequences permitted in unions")
		Root.add(self, child)
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

	def __parse_subs(self, subs):
		if subs == None:
			min = max = 1
		elif len(subs) == 0:
			raise Exception("Use a blob")
		elif len(subs) == 1:
			assert(subs[0].__class__ == LexInteger)
			min = max = int(subs[0])
		elif len(subs) == 3:
			assert(map(lambda x:x.__class__, subs) ==
				[LexInteger, LexRange, LexInteger])
			min = int(subs[0])
			max = int(subs[2])
		else:
			raise Exception("Syntax error")

		return (min * self.bytes, max * self.bytes)

	def __init__(self, tag, bits, name, subs, optional = False):
		Fixed.__init__(self, tag, name, optional)
		assert((bits % self.BITS_PER_BYTE) == 0)
		self.bits = bits
		self.bytes = bits / self.BITS_PER_BYTE
		self.constraint = self.__parse_subs(subs)

	def __str__(self):
		if (self.bytes, self.bytes) == self.constraint:
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
	def __init__(self, tag, name, subs, optional = False):
		Uint.__init__(self, tag, 8, name, subs, optional)
class Octet(Uint,Fixed):
	def __init__(self, tag, name, subs, optional = False):
		Uint.__init__(self, tag, 8, name, subs, optional)
	def __str__(self):
		if (self.bytes, self.bytes) == self.constraint:
			return "Octet(%s)"%(self.name)
		elif self.constraint[0] == self.constraint[1]:
			return "Octet[%u](%s)"%(self.constraint[0],
						self.name)
		else:
			return "Octet[%u:%u](%s)"%(self.constraint[0],
							self.constraint[1],
							self.name)
class Uint16(Uint,Fixed):
	def __init__(self, tag, name, subs, optional = False):
		Uint.__init__(self, tag, 16, name, subs, optional)
class Uint32(Uint,Fixed):
	def __init__(self, tag, name, subs, optional = False):
		Uint.__init__(self, tag, 32, name, subs, optional)
class Uint64(Uint,Fixed):
	def __init__(self, tag, name, subs, optional = False):
		Uint.__init__(self, tag, 64, name, subs, optional)

class Blob(Fixed):
	def __init__(self, tag, name, subs, optional = False):
		Fixed.__init__(self, tag, name, optional)
		assert(subs == None)
	def __str__(self):
		return "Blob(%s)"%self.name
