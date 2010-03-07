class VarDeclaration:
	def __getitem__(self):
		raise IndexError
	def __iter__(self):
		return [].__iter__()
		

class CompoundDeclaration(VarDeclaration):
	def __init__(self, type, template, name = ''):
		self.name = name
		self.type = type + " " + template.name
		self.cname = template.name
		self.__elem = []
	def add(self, element):
		self.__elem.append(element)
	def __iter__(self):
		return self.__elem.__iter__()
	def __getitem__(self, idx):
		return self.__elem[idx]
	def __str__(self):
		return self.type
	def write(self, f, depth = 0):
		tabs = "".join("\t" for i in range(depth))
		f.write("%s%s {\n"%(tabs, self))
		for e in self:
			e.write(f, depth + 1)
		f.write(tabs + "}%s;\n"%self.name)
		pass

class StructDeclaration(CompoundDeclaration):
	def __init__(self, template, name = ''):
		CompoundDeclaration.__init__(self, "struct", template, name)
class UnionDeclaration(CompoundDeclaration):
	def __init__(self, template, name = ''):
		CompoundDeclaration.__init__(self, "union", template, name)

class ScalarDeclaration(VarDeclaration):
	def __init__(self, type, name, ptr = None, arraysz = None):
		self.type = type
		self.name = name
		self.cname = name
		self.ptr = ptr
		self.arraysz = arraysz
	def __str__(self):
		if self.arraysz == None:
			ss = ''
		else:
			ss = '[%u]'%self.arraysz
		return "%s %s%s%s;"%(self.type,
					self.ptr and '*' or '',
					self.name,
					ss)
	def write(self, f, depth = 0):
		tabs = "".join("\t" for i in range(depth))
		f.write(tabs + str(self) + "\n")

