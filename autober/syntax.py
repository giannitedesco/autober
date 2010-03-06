from tokens import *

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
