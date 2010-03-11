from syntax import *

class CDefn:
	def __init__(self, node, parent):
		if parent:
			self.name = node.name
		else:
			self.name = node[0].name
		self.parent = parent
		if parent and parent.parent:
			if parent.__class__ == CUnion:
				self.tagname = "TAG_%s_%s"%(parent.parent.name.upper(),
							self.name.upper())
			else:
				self.tagname = "TAG_%s_%s"%(parent.name.upper(),
							self.name.upper())
		else:
			self.tagname = "TAG_%s"%self.name.upper()
	def __iter__(self):
		return [].__iter__()
	def __getitem__(self, idx):
		raise IndexError
	def tag_macro(self):
		return self.tagname


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
				self.var_array = self.constraint[0] != \
						self.constraint[1]
				if self.var_array:
					self.cnt_name = "&" + \
						self.parent.name + \
						self.parent.prefix + \
						"_" + self.name + "_count"
			else:
				self.is_array = False
				self.var_array = False
		else:
			self.constraint = None
			self.is_array = False
			self.var_array = False
		if self.optional:
			self.optmacro = "%s_%s"%(parent.name.upper(),
						self.name.upper())
		self.type = typemap[node.__class__]
	def call_free(self, f, parent, name, indent = 1):
		if self.type != self.TYPE_BLOB:
			return
		tabs = ''.join("\t" for i in range(indent))
		if self.optional:
			f.write(tabs + "if ( %s->_present & %s )\n"%(parent,
					self.optmacro))
			tabs += "\t"
		f.write(tabs + "free(%s%s.ptr);\n"%(parent, name))

	def __octet(self, f, tabs, name, cnt):
		f.write("if ( !autober_octet(%s, &tag, ptr, %s) )\n"%(name, cnt))
	def __uint8(self, f, tabs, name, cnt):
		f.write("if ( !autober_u8(%s, &tag, ptr, %s) )\n"%(name, cnt))
	def __uint16(self, f, tabs, name, cnt):
		f.write("if ( !autober_u16(%s, &tag, ptr, %s) )\n"%(name, cnt))
	def __uint32(self, f, tabs, name, cnt):
		f.write("if ( !autober_u32(%s, &tag, ptr, %s) )\n"%(name, cnt))
	def __uint64(self, f, tabs, name, cnt):
		f.write("if ( !autober_u64(%s, &tag, ptr, %s) )\n"%(name, cnt))
	def __blob(self, f, tabs, name, cnt):
		f.write("if ( !autober_blob(%s, &tag, ptr) )\n"%name)
		
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
		if self.var_array:
			cnt = self.cnt_name
		else:
			cnt = "NULL"
		f.write(tabs)
		decodemap[self.type](f, tabs, name, cnt)
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

		if self.parent == None:
			self.modname = node[0].name
			self.free_func = "%s_free"%self.modname
			self.decode_func = "_root"
			self.tagblock_arr = "root_tags"
			self.label = "root level"
			self.prefix = ''

			# not sure about these
			self.alloc = False
		else:
			self.free_func = "_free_%s"%self.name
			self.decode_func = "_%s"%self.name
			self.tagblock_arr = "%s_tags"%self.name
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
		ti = 0
		for tb in self.tagblocks:
			if tb.sequence:
				tb.item.tagindex = ti
			ti += 1

	def call_free(self, f, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
		if not self.parent:
			self.subtags[0].call_free()
			return
		f.write("%s%s(&%s[i]);\n"%(tabs, self.free_func, name))

	def write_free(self, f):
		for (n, x) in self.structs + self.sequences:
			x.write_free(f)
		if self.parent:
			f.write("static ")
		f.write("void %s(struct %s *%s)\n"%(self.free_func,
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

		for (n, x) in self.unions:
			x.write_free(f, str(self), n)
		for (n, x) in self.scalars:
			x.call_free(f, self, n)
		for (n, x) in self.structs:
			x.call_free(f, n)

		if self.alloc:
			f.write("\tfree(%s);\n"%str(self))
		f.write("}\n\n")

	def write_decode(self, f):
		for (n, x) in self.sequences:
			x.write_decode(f)
		for (n, x) in self.structs:
			x.write_decode(f)
		f.write("static int %s(struct %s *%s,\n"%(self.decode_func,
								str(self),
								str(self)))
		f.write("\t\t\t\tconst uint8_t *ptr, size_t len)\n")
		f.write("{\n")
		f.write("\tstatic const unsigned int num = AUTOBER_NUM_TAGS"\
			"(%s);\n"%self.tagblock_arr)
		f.write("\tstruct autober_constraint cons[num];\n")
		f.write("\tstruct gber_tag tag;\n")
		f.write("\tconst uint8_t *end;\n\n")

		f.write("\tif ( !autober_constraints(%s, "\
			"cons, num, ptr, len) ) {\n"%self.tagblock_arr)
		f.write("\t\tfprintf(stderr, \"%s: constraints "\
			"not satisified\\n\");\n"%self.tagblock_arr)
		f.write("\t\treturn 0;\n")
		f.write("\t}\n\n")

		# FIXME:use correct count
		for (n, x) in self.sequences:
			f.write("\t%s%s = calloc(cons[%u].count, "\
				"sizeof(*%s%s));\n"%(
				self, n, x.tagindex, self, n))
			f.write("\tif ( NULL == %s%s )\n"%(self, n))
			f.write("\t\treturn 0;\n\n")

		f.write("\tfor(end = ptr + len; ptr < end; "\
			"ptr += tag.ber_len) {\n")
		f.write("\t\tptr = ber_decode_tag(&tag, ptr, end - ptr);\n")
		f.write("\t\tif ( NULL == ptr )\n")
		f.write("\t\t\treturn 0;\n\n")
		f.write("\t\tswitch(tag.ber_tag) {\n")
		for (n, x) in self.subtags:
			f.write("\t\tcase %s:\n"%x.tagname)
			if self.parent:
				x.call_decode(f, str(self) + n, indent = 3)
			else:
				x.call_decode(f, n, indent = 3)
			if x.parent.__class__ == CUnion:
				x.parent.set_type_var(f, x, indent = 3)
			if x.__class__ != CScalar:
				f.write("\t\t\tbreak;\n");
				continue
			if x.optional:
				f.write("\t\t\t%s->_present |= %s;\n"%(\
					str(self), x.optmacro))
			f.write("\t\t\tbreak;\n");
		f.write("\t\tdefault:\n")
		f.write("\t\t\tfprintf(stderr, \"Unexpected tag: "\
			"%.4x\\n\", tag.ber_tag);\n")
		f.write("\t\t\treturn 0;\n")
		f.write("\t\t}\n")
		f.write("\t}\n\n")

		f.write("\treturn 1;\n")
		f.write("}\n\n")
		return
	
	def write_tagblock(self, f):
		f.write("static const struct autober_tag %s[] = {\n"%\
			self.tagblock_arr);
		map(lambda x:x.write(f), self.tagblocks)
		f.write("};\n\n")

class CUnion(CContainer, CDefn):
	def __init__(self, node, parent, prefix = '.'):
		CContainer.__init__(self, node, parent)
		self.type_var = "%s_%s_type"%(parent.prefix, node.name)
		self.choices = {}
		self.typemap = {}
		for (n, x) in self:
			macro = "%s_%s_TYPE_%s"%(self.parent.name.upper(),
					self.name.upper(),
					x.name.upper())
			self.choices[macro] = (n, x)
			self.typemap[x] = macro
	def set_type_var(self, f, node, indent = 3):
		tabs = ''.join("\t" for i in range(indent))
		f.write(tabs + "%s%s = %s;\n"%(self.parent,
						self.type_var,
						self.typemap[node]))

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
		if parent and not parent.parent:
			self.alloc = True
		else:
			self.alloc = False
		self.tag = node.tag
		self.label = node.label
	def call_decode(self, f, name, indent = 1):
		tabs = "".join("\t" for i in range(indent))
		if self.alloc:
			f.write(tabs + "if ( !%s(%s, ptr, tag.ber_len) )\n"%(
				self.decode_func, name))
		else:
			f.write(tabs + "if ( !%s(&%s, ptr, tag.ber_len) )\n"%(
				self.decode_func, name))
		f.write(tabs + "\treturn 0;\n")
	def call_free(self, f, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
		if self.parent and self.parent.parent:
			f.write("%s%s(&%s%s);\n"%(tabs, self.free_func, str(self.parent), name))
		else:
			f.write("%s%s(%s);\n"%(tabs, self.free_func, name))

class CStructPtr(CContainer,CDefn):
	def __init__(self, node, parent):
		CContainer.__init__(self, node, parent, prefix = '->')
		self.tag = node.tag
		self.alloc = True
		self.label = node.label
		self.count_var = "%s_%s_count"%(self.prefix, node.name)
		self.tagindex = -1

	def call_decode(self, f, name, indent = 1):
		tabs = "".join("\t" for i in range(indent))
		f.write(tabs + "if ( !%s(&%s[%s%s], " \
				"ptr, tag.ber_len) )\n"%(
				self.decode_func, name, str(self.parent),
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
		if item.__class__ in [CStruct, CStructPtr, CContainer]:
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
		if self.union:
			self.label = item.parent.name + '.' + self.label
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
		f.write("/* Tags for %s */\n"%node.label)
		node.write_tagblock(f)
		for (n, x) in node.structs + node.sequences:
			self.__write_tagblock(f, x)

	def write_tagblocks(self, f):
		self.__write_tagblock(f, self.root)
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

	def write_free(self, f):
		self.root.write_free(f)

	def __write_root_decode(self, f):
		r = self.root
		f.write("struct %s *%s_decode(const uint8_t *ptr, "\
			"size_t len)\n"%(r, r))
		f.write("{\n")
		f.write("\tstruct %s *%s;\n\n"%(r, r))
		f.write("\t%s = calloc(1, sizeof(*%s));\n"%(r, r))
		f.write("\tif ( NULL == %s )\n"%r)
		f.write("\t\treturn NULL;\n\n")

		f.write("\tif ( !%s(%s, ptr, len) ) {\n"%(r.decode_func, r))
		f.write("\t\t%s(%s);\n"%(r[0][1].free_func, r))
		f.write("\t\treturn NULL;\n")
		f.write("\t}\n\n")
		f.write("\treturn %s;\n"%r)
		f.write("}\n")

	def write_func_decls(self, f):
		r = self.root
		f.write("struct %s *%s_decode(const uint8_t *ptr, "\
			"size_t len);\n"%(r, r))
		f.write("void %s(struct %s *%s);\n"%(r.free_func, r, r))

	def write_decode(self, f):
		self.root.write_decode(f)
		self.__write_root_decode(f)

	def __init__(self, root):
		self.root = CContainer(root, None)
		self.pretty_print()
