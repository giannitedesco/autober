from syntax import *

class CDefn:
	def __init__(self, node, parent):
		self.name = node.name
		self.parent = parent
		if parent:
			self.tagname = "TAG_%s_%s"%(parent.name.upper(),
							self.name.upper())
		else:
			self.tagname = "TAG_%s"%self.name.upper()
	def __iter__(self):
		return [].__iter__()
	def __getitem__(self, idx):
		raise IndexError
	def tag_macro(self):
		if not self.parent:
			prefix = ''
		else:
			prefix = '_' + self.parent.name.upper()
		return "TAG%s_%s"%(prefix, self.name.upper())


class CScalar(CDefn):
	TYPE_OCTET		= 0
	TYPE_U8			= 1
	TYPE_U16		= 2
	TYPE_U32		= 3
	TYPE_U64		= 4
	TYPE_BLOB		= 5
	def __init__(self, node, parent):
		typemap = {Octet: self.TYPE_OCTET,
				Uint8: self.TYPE_U8,
				Uint16: self.TYPE_U16,
				Uint32: self.TYPE_U32,
				Blob: self.TYPE_BLOB}
		CDefn.__init__(self, node, parent)
		self.tag = node.tag
		self.optional = node.optional
		if node.constraint != None:
			self.constraint = node.constraint
			if self.constraint[1] / node.bytes > 1:
				self.is_array = True
			else:
				self.is_array = False
		else:
			self.constraint = None
			self.is_array = False
		if self.optional:
			self.optmacro = "%s_%s"%(parent.name.upper(),
						self.name.upper())
		self.type = typemap[node.__class__]
	def call_free(self, f, parent, name, indent = 1):
		if self.type != self.TYPE_BLOB:
			return
		tabs = ''.join("\t" for i in range(indent))
		if self.optional:
			# not strictly necessary since we calloc
			f.write(tabs + "if ( %s->_present & %s )\n"%(parent,
					self.optmacro))
			tabs += "\t"
		f.write(tabs + "free(%s%s.ptr);\n"%(parent, name))

	def __octet(self, f, tabs, name):
		f.write(tabs + "if ( !autober_octet(%s, &tag, ptr) )\n"%(name))
	def __uint8(self, f, tabs, name):
		f.write(tabs + "if ( !autober_u8(%s, &tag, ptr) )\n"%(name))
	def __uint16(self, f, tabs, name):
		f.write(tabs + "if ( !autober_u16(%s, &tag, ptr) )\n"%(name))
	def __uint32(self, f, tabs, name):
		f.write(tabs + "if ( !autober_u32(%s, &tag, ptr) )\n"%(name))
	def __uint64(self, f, tabs, name):
		f.write(tabs + "if ( !autober_u64(%s, &tag, ptr) )\n"%(name))
	def __blob(self, f, tabs, name):
		f.write(tabs + "if ( !autober_blob(%s, &tag, ptr) )\n"%(name))
		
	def call_decode(self, f, name, indent = 1):
		decodemap = {self.TYPE_OCTET: self.__octet,
				self.TYPE_U8: self.__uint8,
				self.TYPE_U16: self.__uint16,
				self.TYPE_U32: self.__uint32,
				self.TYPE_U64: self.__uint64,
				self.TYPE_BLOB: self.__blob,
				}
		tabs = "".join("\t" for i in range(indent))
		if not self.is_array:
			name = "&" + name
		decodemap[self.type](f, tabs, name)
		f.write(tabs + "\treturn 0;\n")

class CContainer(CDefn):
	def __unions(self):
		return filter(lambda x:x[1].__class__ == CUnion, self)

	def __structs(self):
		return filter(lambda x:x[1].__class__ == CStruct, self)

	def __sequences(self):
		return filter(lambda x:x[1].__class__ == CStructPtr, self)

	def __scalars(self):
		return filter(lambda x:x[1].__class__ == CScalar, self)

	def __toplevel(self, node):
		ret = []
		for x in node:
			n = self.prefix + x.name
			if x.__class__ == Template:
				if x.sequence:
					obj = (n, CStructPtr(x, self))
				else:
					obj = (n, CStruct(x, self))
			elif x.__class__ == Union:
				obj = (n, CUnion(x, self))
			else:
				obj = (n, CScalar(x, self))
			ret.append(obj)
		return ret
	
	def __subtags(self):
		ret = filter(lambda x:x[1].__class__ != CUnion, self)
		for (n, x) in self.unions:
			for (nn, xx) in x:
				ret.append((n + nn, xx))
		return ret;

	def __tagblocks(self):
		nu = filter(lambda x:x[1].__class__ != CUnion, self)
		ret = []
		for (n, x) in nu:
			ret.append((x, False))
		for (n, x) in self.unions:
			for (nn, xx) in x:
				ret.append((xx, True))
		return map(lambda x:TagDefinition(x[0], union=x[1]), ret);

	def __iter__(self):
		return self.toplevel.__iter__()
	def __getitem__(self, idx):
		return self.toplevel[idx]

	def __str__(self):
		return self.name

	def __init__(self, node, parent, prefix = '.'):
		CDefn.__init__(self, node, parent)
		if parent == None:
			self.is_root = True
		else:
			self.is_root = False
		self.prefix = prefix
		self.toplevel = []
		self.toplevel = self.__toplevel(node)
		self.unions = self.__unions()
		self.structs = self.__structs()
		self.sequences = self.__sequences()
		self.scalars = self.__scalars()
		self.subtags = self.__subtags()
		self.tagblocks = self.__tagblocks()
		self.tagblocks.sort()

	def call_free(self, f, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
		if self.is_root:
			f.write("%s_free_%s(%s);\n"%(tabs, self.name, name))
		else:
			f.write("%s_free_%s(&%s[i]);\n"%(tabs, self.name, name))

	def write_free(self, f):
		for (n, x) in self.structs + self.sequences:
			x.write_free(f)
		f.write("static void _free_%s(struct %s *%s)\n"%(str(self),
								str(self),
								str(self)))
		f.write("{\n")
		if len(self.sequences):
			f.write("\tunsigned int i;\n\n");

		if self.alloc:
			f.write("\tif ( NULL == %s )\n"%str(self))
			f.write("\t\treturn;\n\n")

		for (n, x) in self.sequences:
			f.write("\tfor(i = 0; i < %s%s; i++)\n"%(
						str(self), x.count_var))
			x.call_free(f, "%s%s"%(str(self), n), indent = 2)
			f.write("\tfree(%s%s);\n\n"%(str(self), n))

		for (n, x) in self.unions:
			x.write_free(f, str(self), n)
		for (n, x) in self.scalars:
			x.call_free(f, self, n)

		if self.is_root:
			f.write("\tfree(%s);\n"%str(self))
		f.write("}\n\n")

	def write_decode(self, f):
		for (n, x) in self.sequences:
			x.write_decode(f)
		for (n, x) in self.structs:
			x.write_decode(f)
		f.write("static int _decode_%s(struct %s *%s, \n"%(str(self),
								str(self),
								str(self)))
		f.write("\t\t\t\tconst uint8_t *ptr, size_t len)\n")
		f.write("{\n")
		f.write("\tstatic const unsigned int num = AUTOBER_NUM_TAGS"\
			"(%s_tags);\n"%self)
		f.write("\tstruct autober_constraint cons[num];\n")
		f.write("\tstruct gber_tag tag;\n")
		f.write("\tconst uint8_t *end;\n\n")

		f.write("\tif ( !autober_constraints(%s_tags, "\
			"cons, num, ptr, len) ) {\n"%self)
		f.write("\t\tfprintf(stderr, \"%s_tags: constraints "\
			"not satisified\\n\");\n"%self)
		f.write("\t\treturn 0;\n")
		f.write("\t}\n\n")

		# TODO: Check one union members set

		# FIXME:use correct count
		for (n, x) in self.sequences:
			f.write("\t%s%s = calloc(1, sizeof(*%s%s));\n"%(
				self, n, self, n))
			f.write("\tif ( NULL == %s%s )\n"%(self, n))
			f.write("\t\treturn 0;\n\n")

		f.write("\tfor(end = ptr + len; ptr < end; "\
			"ptr += tag.ber_len) {\n")
		f.write("\t\tptr = ber_decode_tag(&tag, ptr, end - ptr);\n")
		f.write("\t\tif ( NULL == ptr )\n")
		f.write("\t\t\treturn 0;\n\n")
		f.write("\t\tswitch(tag.ber_tag) {\n")
		for (n, x) in self.subtags:
			if x.__class__ == CUnion:
				continue
			f.write("\t\tcase %s:\n"%x.tagname)
			x.call_decode(f, str(self) + n, indent = 3)
			f.write("\t\t\tbreak;\n");
		f.write("\t\tdefault:\n")
		f.write("\t\t\tfprintf(stderr, \"Unexpected tag\\n\");\n")
		f.write("\t\t\treturn 0;\n")
		f.write("\t\t}\n")
		f.write("\t}\n\n")

		f.write("\treturn 0;\n")
		f.write("}\n\n")
		return
	
	def write_tagblock(self, f):
		map(lambda x:x.write(f), self.tagblocks)

class CUnion(CContainer, CDefn):
	def __init__(self, node, parent, prefix = '.'):
		CContainer.__init__(self, node, parent)
		self.type_var = "%s_%s_type"%(parent.prefix, node.name)
		self.choices = {}
		for (n, x) in self:
			macro = "%s_TYPE_%s"%(self.name.upper(), x.name.upper())
			self.choices[macro] = (n, x)
	def write_free(self, f, parent, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
		f.write("%sswitch(%s%s) {\n"%(tabs, parent, self.type_var))
		keys = self.choices.keys()
		keys.sort()
		for k in keys:
			f.write("%scase %s:\n"%(tabs, k))
			(n, x) = self.choices[k]
			x.call_free(f, parent, name + n,
					indent = indent + 1)
			f.write("%s\tbreak;\n"%tabs)
		f.write("%s}\n"%tabs);
		return
	def write_decode(self, f):
		raise Exception("WTF")
	def write_tagblock(self, f):
		raise Exception("WTF")

class CStruct(CContainer,CDefn):
	def __init__(self, node, parent):
		CContainer.__init__(self, node, parent, prefix = '->')
		self.tag = node.tag
		self.alloc = False
		self.label = node.label
	def call_decode(self, f, name, indent = 1):
		tabs = "".join("\t" for i in range(indent))
		f.write(tabs + "if ( !_decode_%s(&%s, ptr, tag.ber_len) )\n"%(
			self.name, name))
		f.write(tabs + "\treturn 0;\n")

class CStructPtr(CContainer,CDefn):
	def __init__(self, node, parent):
		CContainer.__init__(self, node, parent, prefix = '->')
		self.tag = node.tag
		self.alloc = True
		self.label = node.label
		if not self.is_root:
			self.count_var = "%s_%s_count"%(self.prefix, node.name)

	def call_decode(self, f, name, indent = 1):
		tabs = "".join("\t" for i in range(indent))
		f.write(tabs + "if ( !_decode_%s(&%s[%s%s], " \
				"ptr, tag.ber_len) )\n"%(
				self.name, name, str(self.parent),
				self.count_var))
		f.write(tabs + "\treturn 0;\n")
		f.write(tabs + "%s%s++;\n"%(str(self.parent), self.count_var))

class TagDefinition:
	__typemap = {CScalar.TYPE_BLOB: "AUTOBER_TYPE_BLOB",
			CScalar.TYPE_OCTET: "AUTOBER_TYPE_OCTET",
			CScalar.TYPE_U8: "AUTOBER_TYPE_INT",
			CScalar.TYPE_U16: "AUTOBER_TYPE_INT",
			CScalar.TYPE_U32: "AUTOBER_TYPE_INT",
			CScalar.TYPE_U64: "AUTOBER_TYPE_INT",
		}

	def __init__(self, item, union = False):
		self.item = item
		self.union = union
		self.check_size = False
		self.sequence = False
		if item.__class__ in [CStruct, CStructPtr]:
			self.template = True
			self.optional = False
			if item.__class__ == CStructPtr:
				self.sequence = True
			self.label = item.label
			self.type = None
		elif item.__class__ == CScalar:
			self.template = False
			self.optional = item.optional
			self.label = item.name
			self.type = self.__typemap[item.type]
			self.constraint = item.constraint
			self.check_size = (self.constraint != None)
		else:
			raise Exception("Union not permitted in tag block")
	def __int__(self):
		return self.item.tag
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
		f.write("\t\t.ab_tag = %s},\n"%self.item.tag_macro())


class CDefinitions:
	def __do_print(self, node, depth = 0):
		indent = ''.join("\t" for x in range(depth))
		for (n, x) in node:
			print "%s%s"%(indent, n)
			self.__do_print(x, depth + 1)
			
	def pretty_print(self):
		print str(self.root)
		self.__do_print(self.root, 1)

	def __write_tagblock(self, f, node):
		for (n, x) in node.structs + node.sequences:
			self.__write_tagblock(f, x)
		f.write("/* Tags for %s */\n"%node.label)
		f.write("static const struct autober_tag %s_tags[] = {\n"%\
			str(node));
		node.write_tagblock(f)
		f.write("};\n\n")

	def write_tagblocks(self, f):
		self.__write_tagblock(f, self.root)

		t = TagDefinition(self.root)
		f.write("/* Tags for %s */\n"%self.root.label)
		f.write("static const struct autober_tag root_tags[] = {\n")
		t.write(f)
		f.write("};\n\n")
		f.write("\n")
		return

	def __write_tag_macros(self, f, node):
		for (n, x) in node.structs + node.sequences:
			self.__write_tag_macros(f, x)
		f.write("/* Tags for %s */\n"%node.label)
		for (n, x) in node.subtags:
			f.write("#define %-30s 0x%.4x\n"%(x.tag_macro(), x.tag))
		f.write("\n")

	def write_tag_macros(self, f):
		self.__write_tag_macros(f, self.root)
		f.write("/* Root tag: %s */\n"%self.root.label)
		f.write("#define %s 0x%.4x\n"%(self.root.tag_macro(),
						self.root.tag))
		f.write("\n")

	def write_free(self, f):
		self.root.write_free(f)
		f.write("void %s_free(struct %s *%s)\n"%(str(self.root),
							str(self.root),
							str(self.root)))
		f.write("{\n")
		self.root.call_free(f, "%s"%str(self.root))
		f.write("}\n\n")

	def write_decode(self, f):
		self.root.write_decode(f)

	def __init__(self, root):
		self.root = CStructPtr(root, None)
		self.pretty_print()
