from parser import Template, Union, Fixed

class VarDefinition:
	def __getitem__(self):
		raise IndexError
	def __iter__(self):
		return [].__iter__()
		

class CompoundDefinition(VarDefinition):
	def __init__(self, tag, template, name = ''):
		self.name = name
		self.type = tag + " " + template.name
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

class StructDefinition(CompoundDefinition):
	def __init__(self, template, name = ''):
		CompoundDefinition.__init__(self, "struct", template, name)
class UnionDefinition(CompoundDefinition):
	def __init__(self, template, name = ''):
		CompoundDefinition.__init__(self, "union", template, name)

class ScalarDefinition(VarDefinition):
	def __init__(self, type, name, ptr, arraysz = None):
		if type == "octet":
			self.type = 'uint8_t'
		elif type == "blob":
			self.type = "struct autober_blob"
		else:
			self.type = type
		self.name = name
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

def scalar(fixed):
	if fixed.constraint != None:
		arraysz = fixed.constraint[1]
	else:
		arraysz = None
	return ScalarDefinition(fixed.type.name, fixed.name, False, arraysz)

def pointer_to(d, name):
	return ScalarDefinition(d.type, name, True)

class c_codec:
	def __do_structs(self, node, name = '', union = False):
		if union:
			struct = UnionDefinition(node, name)
		else:
			struct = StructDefinition(node, name)
		for x in node:
			if x.__class__ == Template:
				if x.sequence:
					ret = self.__do_structs(x)
					struct.add(pointer_to(ret, x.name))
					self.structs.append(ret)
				else:
					ret = self.__do_structs(x, x.name)
					struct.add(ret)
			elif x.__class__ == Union:
				ret = self.__do_structs(x, x.name, True)
				struct.add(ret)
				continue
			else:
				struct.add(scalar(x))
		return struct

	def __build_structs(self, node):
		self.structs = []
		self.structs.append(self.__do_structs(node))

	def __init__(self, ast):
		self.ast = ast
		self.parse = ast.parse_tree

		assert(1 == len(self.parse))

		self.root = self.parse[0]
		self.modname = self.root.name.lower()
		self.__build_structs(self.root)

	def __write_struct(self, s, f):
		s.write(f)

	def write_header(self, f):
		f.write("#ifndef _%s_H\n"%self.modname.upper())
		f.write("#define _%s_H\n"%self.modname.upper())

		f.write("\n")
		for s in self.structs:
			self.__write_struct(s, f)
		f.write("\n")

		f.write("#endif /* _%s_H */\n"%self.modname.upper())
		return
