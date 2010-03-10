from syntax import *

class CDefn:
	def __init__(self, node, parent):
		self.name = node.name
		if parent:
			self.tagname = "TAG_%s_%s"%(parent.name.upper(),
							self.name.upper())
		else:
			self.tagname = "TAG_%s"%self.name.upper()

class CScalar(CDefn):
	def __init__(self, node, parent):
		CDefn.__init__(self, node, parent)
		self.optional = node.optional
		if self.optional:
			self.optmacro = "%s_%s"%(parent.name.upper(),
						self.name.upper())
		if node.__class__ == Blob:
			self.is_blob = True
		else:
			self.is_blob = False
	def call_free(self, f, parent, name, indent = 1):
		if not self.is_blob:
			return
		tabs = ''.join("\t" for i in range(indent))
		if self.optional:
			# not strictly necessary since we calloc
			f.write(tabs + "if ( %s->_present & %s )\n"%(parent,
					self.optmacro))
			tabs += "\t"
		f.write(tabs + "free(%s%s.ptr);\n"%(parent, name))

class CContainer(CDefn):
	def __scalar(self, node, prefix = '', toplevel = True):
		ret = []
		for x in node:
			if toplevel:
				name = prefix + self.prefix + x.name
			else:
				name = prefix + '.' + x.name
			if Fixed in x.__class__.__bases__:
				r = [(name, CScalar(x, parent = node))]
			elif x.__class__ == Template and not x.sequence:
				r = self.__scalar(x, prefix = name,
							toplevel = False)
			else:
				continue
			ret.extend(r)
		return ret

	def __ptrs(self, node, prefix = '', toplevel = True):
		ret = []
		for x in node:
			name = self.prefix + x.name
			if x.__class__ != Template:
				continue
			if toplevel:
				name = prefix + self.prefix + x.name
			else:
				name = prefix + '.' + x.name
			if x.sequence:
				ret.append((name, CStructPtr(x, self)))
			else:
				ret.extend(self.__ptrs(x, prefix = name,
						toplevel = False))
		return ret

	def __unions(self, node):
		ret = []
		for x in node:
			if x.__class__ != Union:
				continue
			name = self.prefix + x.name
			ret.append((name, CUnion(self, x)))
		return ret
	
	def __toplevel(self, node):
		ret = []
		for x in node:
			continue
		return ret

	def __str__(self):
		return self.name

	def __init__(self, node, parent, prefix = '.'):
		CDefn.__init__(self, node, parent)
		if parent == None:
			self.is_root = True
		else:
			self.is_root = False
		self.prefix = prefix
		if not self.is_root:
			self.count_var = "%s_%s_count"%(self.prefix, node.name)
		self.toplevel = []
		self.all = []
		self.scalar = self.__scalar(node)
		self.ptrs = self.__ptrs(node)
		self.unions = self.__unions(node)
		self.all.extend(self.scalar)
		self.all.extend(self.ptrs)
		self.all.extend(self.unions)

class CUnion(CDefn,CContainer):
	def __init__(self, parent, node, prefix = '.'):
		CContainer.__init__(self, node, parent)
		self.type_var = "%s_%s_type"%(parent.prefix, node.name)
		self.choices = {}
		for (n, x) in self.all:
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

class CStructPtr(CDefn,CContainer):
	def __init__(self, node, parent):
		CContainer.__init__(self, node, parent, prefix = '->')

	def call_free(self, f, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
		if self.is_root:
			f.write("%s_free_%s(%s);\n"%(tabs, self.name, name))
		else:
			f.write("%s_free_%s(&%s[i]);\n"%(tabs, self.name, name))

	def write_free(self, f):
		for (n, x) in self.ptrs:
			x.write_free(f)
		f.write("static void _free_%s(struct %s *%s)\n"%(str(self),
								str(self),
								str(self)))
		f.write("{\n")
		if len(self.ptrs):
			f.write("\tunsigned int i;\n\n");
		f.write("\tif ( NULL == %s )\n"%str(self))
		f.write("\t\treturn;\n\n")

		for (n, x) in self.ptrs:
			f.write("\tfor(i = 0; i < %s%s; i++)\n"%(
						str(self), x.count_var))
			x.call_free(f, "%s%s"%(str(self), n), indent = 2)
			f.write("\tfree(%s%s);\n\n"%(str(self), n))

		for (n, x) in self.unions:
			x.write_free(f, str(self), n)
		for (n, x) in self.scalar:
			x.call_free(f, self, n)

		if self.is_root:
			f.write("\tfree(%s);\n"%str(self))
		f.write("}\n\n")
	
	def write_decode(self, f):
		for (n, x) in self.ptrs:
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

		# TODO: Check one or more union members set

		f.write("\tfor(end = ptr + len; ptr < end; "\
			"ptr += tag.ber_len) {\n")
		f.write("\t\tptr = ber_decode_tag(&tag, ptr, end - ptr);\n")
		f.write("\t\tif ( NULL == ptr )\n")
		f.write("\t\t\treturn 0;\n\n")
		f.write("\t\tswitch(tag.ber_tag) {\n")
		for (n, x) in self.toplevel:
			f.write("\t\tcase %s:\n"%x.tagname)
			f.write("\t\t\tbreak;\n");
		for (n, x) in self.unions:
			for (nn, xx) in x.all:
				f.write("\t\tcase %s:\n"%xx.tagname)
				f.write("\t\t\tbreak;\n");
		f.write("\t\tdefault:\n")
		f.write("\t\t\tfprintf(stderr, \"Unexpected tag\\n\");\n")
		f.write("\t\t\treturn 0;\n")
		f.write("\t\t}\n")
		f.write("\t}\n\n")

		f.write("\treturn 0;\n")
		f.write("}\n\n")
		return

class CDefinitions:
	def __do_print(self, node, depth = 0):
		indent = ''.join("\t" for x in range(depth))
		for (n, x) in node.scalar:
			print "%s%s"%(indent, n)
		for (n, x) in node.ptrs:
			print "%s%s"%(indent, n)
			self.__do_print(x, depth + 1)
		# TODO: print unions
			
	def pretty_print(self):
		print str(self.root)
		self.__do_print(self.root, 1)

	def write_free(self, f):
		self.root.write_free(f)
		f.write("void free_%s(struct %s *%s)\n"%(str(self.root),
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
