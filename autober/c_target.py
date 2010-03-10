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

def tag_macro(tname, name):
	if tname == '':
		prefix = ''
	else:
		prefix = '_' + tname.upper()
	return "TAG%s_%s"%(prefix, name.upper())

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

class TagDefinition:
	__typemap = {Blob: "AUTOBER_TYPE_BLOB",
			Octet: "AUTOBER_TYPE_OCTET",
			Uint8: "AUTOBER_TYPE_INT",
			Uint16: "AUTOBER_TYPE_INT",
			Uint32: "AUTOBER_TYPE_INT",
			Uint64: "AUTOBER_TYPE_INT",
		}

	def __check_size(self, tag):
		try:
			if tag.constraint:
				self.constraint = tag.constraint
				self.check_size = True
		except AttributeError:
			return

	def __init__(self, tag, union = False):
		self.tag = tag.tag
		self.tag_macro = tag_macro(tag.parent.name, tag.name)
		self.union = union
		self.check_size = False
		self.sequence = False
		if tag.__class__ == Template:
			self.template = True
			self.optional = False
			if tag.sequence:
				self.sequence = True
			self.label = tag.label
			self.type = None
		elif Fixed in tag.__class__.__bases__:
			self.template = False
			self.optional = tag.optional
			self.label = tag.name
			self.type = self.__typemap[tag.__class__]
			self.__check_size(tag)
		else:
			raise Exception("Union not permitted in tag block")
	def __int__(self):
		return self.tag
	def __cmp__(a, b):
		return int(a) - int(b)
	def flags(self):
		list = []
		if self.template:
			list.append("AUTOBER_TEMPLATE")
		if self.union:
			list.append("AUTOBER_UNION")
		if self.sequence:
			list.append("AUTOBER_SEQUENCE")
		if self.optional:
			list.append("AUTOBER_OPTIONAL")
		if self.check_size:
			list.append("AUTOBER_CHECK_SIZE")
		return "|".join(list)

	def write(self, f):
		f.write("\t{.ab_label = \"%s\",\n"%self.label)
		if self.type != None:
			f.write("\t\t.ab_type = %s,\n"%self.type)
		if self.flags() != '':
			f.write("\t\t.ab_flags = %s,\n"%self.flags())
		if self.check_size:
			f.write("\t\t.ab_size = {%u, %u},\n"%self.constraint)
		f.write("\t\t.ab_tag = %s},\n"%self.tag_macro)

class c_target:
	def __define_tag(self, tname, name, tag):
		self.__macro_tags.append((tag_macro(tname, name), "0x%x"%tag))

	def __define_opt(self, tname, name, val):
		mac = "%s_%s"%(tname.upper(), name.upper())
		self.__macro_optionals.append((mac, "(1<<%uU)"%val))

	def __define_choice(self, tname, name, val):
		mac = "%s_TYPE_%s"%(tname.upper(), name.upper())
		self.__macro_choices.append((mac, val))

	def __do_structs(self, node, name = '', union = False):
		if union:
			struct = UnionDeclaration(node, name)
		else:
			struct = StructDeclaration(node, name)
		opts = False
		for x in node:
			if x.__class__ == Template:
				self.__define_tag(node.name, x.name, x.tag)
				if x.sequence:
					ret = self.__do_structs(x)
					struct.add(pointer_to(ret, x.name))
					struct.add(ScalarDeclaration(
						"unsigned int",
						"_%s_count"%x.name))
					self.structs.append(ret)
				else:
					ret = self.__do_structs(x, x.name)
					struct.add(ret)
			elif x.__class__ == Union:
				ret = self.__do_structs(x, x.name, True)
				struct.add(ScalarDeclaration("unsigned int",
						"_%s_type"%x.name))
				struct.add(ret)
				continue
			else:
				if union:
					self.__define_choice(node.name, x.name,
								x.optindex)
				elif x.optional:
					self.__define_opt(node.name, x.name,
								x.optindex)
					opts = True
				self.__define_tag(node.name, x.name, x.tag)
				struct.add(scalar(x))
		if opts:
			struct.add(ScalarDeclaration("unsigned int",
							"_present"))
		return struct

	def __build_structs(self, node):
		self.structs = []
		self.__define_tag('', node.name, node.tag)
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
		self.__defns = CDefinitions(self.root)

	def __write_struct(self, s, f):
		s.write(f)

	def __write_macros(self, f):
		for macro in self.__macro_tags:
			f.write("#define %s\t\t%s\n"%macro)
		f.write("\n")
		for macro in self.__macro_optionals:
			f.write("#define %s\t\t%s\n"%macro)
		f.write("\n")
		for macro in self.__macro_choices:
			f.write("#define %s\t\t%s\n"%macro)

	def write_header(self, f):
		f.write("/* Generated by autober: do not modify */\n")
		f.write("#ifndef _%s_H\n"%self.modname.upper())
		f.write("#define _%s_H\n"%self.modname.upper())
		f.write("\n")

		self.__write_macros(f)
		f.write("\n")

		for s in self.structs:
			self.__write_struct(s, f)
			f.write("\n")

		# TODO: write function prototypes

		f.write("#endif /* _%s_H */\n"%self.modname.upper())

	def include(self, incl, sys = False):
		list = sys and self.__sysincl or self.__incl
		list.append(incl)

	def __write_incl(self, f):
		for inc in self.__sysincl:
			f.write("#include <%s>\n"%inc)
		for inc in self.__incl:
			f.write("#include \"%s\"\n"%inc)

	def __write_tagblock(self, f, t, name):
		f.write("static const struct autober_tag %s[] = {\n"%name);
		taglist = filter(lambda x:not x.__class__ == Union, t)
		ul = filter(lambda x:x.__class__ == Union, t)
		unionlist = []
		for u in ul:
			unionlist.extend(u)

		tags = map(lambda x:TagDefinition(x), taglist)
		unions = map(lambda x:TagDefinition(x, union = True), unionlist)

		list = tags + unions

		list.sort()
		for tag in list:
			tag.write(f)
		f.write("};\n\n")

	def __write_tagblocks(self, f):
		self.__write_tagblock(f, self.parse, "root_tags")
		for t in self.ast.templates.values():
			self.__write_tagblock(f, t, t.name + "_tags")
		return

	def write_code(self, f):
		f.write("/* Generated by autober: do not modify */\n")
		self.__write_incl(f)
		f.write("\n")
		self.__write_tagblocks(f)
		self.__defns.write_free(f)
		self.__defns.write_decode(f)
