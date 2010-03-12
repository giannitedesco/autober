from syntax import *
from c_decls import *
from c_defns import *

def type_lookup(fixed):
	__typemap = {Octet: "uint8_t",
			Uint8: "uint8_t",
			Uint16: "uint16_t",
			Uint32: "uint32_t",
			Uint64: "uint64_t",
			Blob: "struct autober_blob"}
	return __typemap[fixed.__class__]

def scalar(fixed):
	if fixed.constraint != None:
		arraysz = fixed.constraint[1] / fixed.bytes
		if arraysz == 1:
			arraysz = None
	else:
		arraysz = None
	return ScalarDeclaration(type_lookup(fixed), fixed.name, None, arraysz)

def pointer_to(d, name):
	return ScalarDeclaration(d.type, name, d)

class c_target:
	def __define_opt(self, tname, name, val):
		mac = "%s_%s"%(tname.upper(), name.upper())
		self.__macro_optionals.append((mac, "(1<<%uU)"%val))

	def __define_choice(self, pname, tname, name, val):
		mac = "%s_%s_TYPE_%s"%(pname.upper(), tname.upper(), name.upper())
		self.__macro_choices.append((mac, val))

	def __do_structs(self, node, name = '', union = False):
		if union:
			struct = UnionDeclaration(node, name)
		else:
			struct = StructDeclaration(node, name)
		opts = False
		for x in node:
			if x.__class__ == Template:
				if x.sequence:
					ret = self.__do_structs(x)
					struct.add(pointer_to(ret, x.name))
					struct.add(ScalarDeclaration(
						"unsigned int",
						"_%s_count"%x.name))
					self.structs.append(ret)
				else:
					if x.optional:
						self.__define_opt(node.name,
								x.name,
								x.optindex)
					ret = self.__do_structs(x, x.name)
					struct.add(ret)
					opts = True
			elif x.__class__ == Union:
				ret = self.__do_structs(x, x.name, True)
				struct.add(ScalarDeclaration("unsigned int",
						"_%s_type"%x.name))
				struct.add(ret)
				continue
			else:
				if union:
					self.__define_choice(node.parent.name,
								node.name,
								x.name,
								x.optindex + 1)
				elif x.optional:
					self.__define_opt(node.name, x.name,
								x.optindex)
					opts = True
				if x.constraint and \
					x.constraint[0] != x.constraint[1]:
					struct.add(ScalarDeclaration(
							"unsigned int",
							"_%s_count"%x.name))

				struct.add(scalar(x))
		if opts:
			struct.add(ScalarDeclaration("unsigned int",
							"_present"))
		return struct

	def __build_structs(self, node):
		self.structs = []
		self.root_struct = self.__do_structs(node)
		self.structs.append(self.root_struct)

	def __init__(self, ast):
		# setup attributes
		self.ast = ast
		self.parse = ast.parse_tree
		assert(1 == len(self.parse))
		self.root = self.parse[0]
		self.modname = self.root.name.lower()

		# setup preprocessor
		self.__macro_tags = []
		self.__macro_choices = []
		self.__macro_optionals = []
		self.__sysincl = ["stdlib.h", "stdint.h", "stdio.h"]
		self.__incl = ["gber.h", "autober.h"]

		self.__build_structs(self.root)
		self.__defns = CDefinitions(self.parse)

	def __write_struct(self, s, f):
		s.write(f)

	def __write_macros(self, f):
		for macro in self.__macro_tags:
			f.write("#define %-30s %s\n"%macro)
		f.write("\n")
		for macro in self.__macro_optionals:
			f.write("#define %-30s %s\n"%macro)
		f.write("\n")
		for macro in self.__macro_choices:
			f.write("#define %-30s %s\n"%macro)

	def write_header(self, f):
		f.write("/* Generated by autober: do not modify */\n")
		f.write("#ifndef _%s_H\n"%self.modname.upper())
		f.write("#define _%s_H\n"%self.modname.upper())
		f.write("\n")

		self.__write_macros(f)
		f.write("\n")

		self.__defns.write_tag_macros(f)

		for s in self.structs:
			self.__write_struct(s, f)
			f.write("\n")

		self.__defns.write_func_decls(f)

		f.write("#endif /* _%s_H */\n"%self.modname.upper())

	def include(self, incl, sys = False):
		list = sys and self.__sysincl or self.__incl
		list.append(incl)

	def __write_incl(self, f):
		for inc in self.__sysincl:
			f.write("#include <%s>\n"%inc)
		for inc in self.__incl:
			f.write("#include \"%s\"\n"%inc)

	def write_code(self, f):
		f.write("/* Generated by autober: do not modify */\n")
		self.__write_incl(f)
		f.write("\n")
		self.__defns.write_tagblocks(f)
		self.__defns.write_free(f)
		self.__defns.write_decode(f)
