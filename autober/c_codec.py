from parser import Template, Union, Fixed, Root

def tag_macro(tname, name):
	if tname == '':
		prefix = ''
	else:
		prefix = '_' + tname.upper()
	return "TAG%s_%s"%(prefix, name.upper())

class VarDeclaration:
	def __getitem__(self):
		raise IndexError
	def __iter__(self):
		return [].__iter__()
		

class CompoundDeclaration(VarDeclaration):
	def __init__(self, tag, template, name = ''):
		self.name = name
		self.type = tag + " " + template.name
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
		if type == "octet":
			self.type = 'uint8_t'
		elif type == "blob":
			self.type = "struct autober_blob"
		else:
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

def scalar(fixed):
	if fixed.constraint != None:
		arraysz = fixed.constraint[1]
	else:
		arraysz = None
	return ScalarDeclaration(str(fixed.type), fixed.name, None, arraysz)

def pointer_to(d, name):
	return ScalarDeclaration(d.type, name, d)

class TagDefinition:
	__typemap = {"blob": "AUTOBER_TYPE_BLOB",
			"octet": "AUTOBER_TYPE_OCTET",
			"uint8_t": "AUTOBER_TYPE_INT",
			"uint16_t": "AUTOBER_TYPE_INT",
			"uint32_t": "AUTOBER_TYPE_INT",
			"uint64_t": "AUTOBER_TYPE_INT",
		}
	__multiplier = {"blob": 0,
			"octet": 1,
			"uint8_t": 1,
			"uint16_t": 2,
			"uint32_t": 4,
			"uint64_t": 8}

	def __check_size(self, tag):
		mult = self.__multiplier[str(tag.type)]
		if 0 == mult:
			return

		if tag.constraint == None:
			con = (1,1)
		else:
			con = tag.constraint

		self.constraint = tuple(map(lambda x:x * mult, con))
		self.check_size = True

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
		elif tag.__class__ == Fixed:
			self.template = False
			self.optional = tag.optional
			self.label = tag.name
			self.type = self.__typemap[str(tag.type)]
			self.__check_size(tag)
		else:
			raise Exception("Unnion not permitted in tag block")
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
			f.write("\t\t.ab_count = {%u, %u},\n"%self.constraint)
		f.write("\t\t.ab_tag = %s},\n"%self.tag_macro)

class c_codec:
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
				self.__define_tag(node.name, x.name, x.tag)
				struct.add(scalar(x))
		return struct

	def __build_structs(self, node):
		self.structs = []
		self.__define_tag('', node.name, node.tag)
		self.root_struct = self.__do_structs(node)
		self.structs.append(self.root_struct)

	def __init__(self, ast):
		self.ast = ast
		self.parse = ast.parse_tree

		assert(1 == len(self.parse))

		self.root = self.parse[0]
		self.modname = self.root.name.lower()
		self.__macro_tags = []
		self.__macro_choices = []
		self.__macro_optionals = []
		self.__build_structs(self.root)
		self.__sysincl = ["stdlib.h", "stdint.h", "stdio.h"]
		self.__incl = ["gber.h", "autober.h"]

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

	def __write_do_free(self, f, s):
		fmemb = []
		umemb = []
		for c in s:
			if c.__class__ == UnionDeclaration:
				for m in c:
					umemb.append((c, m))
				continue
			if c.__class__ != ScalarDeclaration:
				continue
			if c.ptr == None:
				continue
			self.__write_do_free(f, c.ptr)
			fmemb.append(c.name)

		f.write("static void _free_%s(%s *%s)\n"%(s.cname,
						s.type, s.cname))
		f.write("{\n")
		if len(fmemb) + len(umemb):
			f.write("\tif (%s) {\n"%s.cname)
			for m in fmemb:
				f.write("\t\t%s_free(%s->%s);\n"%(m,
								s.cname, m))
			for (p,u) in umemb:
				f.write("\t\t//%s->%s.%s ???\n"%(s.cname,
							p.cname,
							u.cname))
			f.write("\t}\n")
		f.write("\tfree(%s);\n"%s.cname)
		f.write("}\n\n")
		return

	def write_code(self, f):
		f.write("/* Generated by autober: do not modify */\n")
		self.__write_incl(f)
		f.write("\n")
		self.__write_tagblocks(f)
		self.__write_do_free(f, self.root_struct)
