from syntax import *

def preproc_define(f, name, val):
	f.write("#define %-30s %s\n"%(name, val))

class CScalar:
	def __init__(self, node, union = None):
		self.union = union
		self.tagno = node.tag
		self.name = node.name

class CStructBase:
	def __init__(self, name, label, tagno = None):
		self.name = name
		self.label = label
		self.tagno = tagno
		self.prefix = "->"

	def __recurse(self, node, union = None):
		if node.__class__ == Template:
			if node.sequence:
				assert(union == None)
				memb = CStructPtr(node)
			else:
				memb = CStruct(node, union)
		else:
			memb = CScalar(node, union)
		return memb

	def _name_union(self, u):
		return "%s%s%s"%(self.name, self.prefix, u.name)

	def _name_tag(self, ch):
		if ch.union:
			return "%s%s%s.%s"%(self.name, self.prefix,
						ch.union.name, ch.name)
		else:
			return "%s%s%s"%(self.name, self.prefix, ch.name)

	def _members(self, iter):
		m = []
		for x in iter:
			if x.__class__ == Union:
				for y in x:
					memb = self.__recurse(y, union = x)
					m.append(memb)
			else:
				memb = self.__recurse(x)
				m.append(memb)

		self._tags = map(lambda x:(self._name_tag(x), x), m)

		self._tagmap = {}
		for (n, x) in self._tags:
			self._tagmap[x.tagno] = (n, x)

		self._scab_tags = filter(lambda x:not x[1].union, self._tags)

		utags = filter(lambda x:x[1].union, self._tags)
		self._unionmap = {}
		for (n, x) in utags:
			uname = self._name_union(x.union)
			if not self._unionmap.has_key(uname):
				self._unionmap[uname] = []
			self._unionmap[uname].append((n, x))

	def write_tagblock(self, f):
		f.write("/* Tags for %s */\n"%self)
	def write_tag_macros(self, f):
		f.write("/* Tag numbers for %s */\n"%self)
		for (n, x) in self._scab_tags:
			preproc_define(f, self._macro_prefix + x.name.upper(),
					"0x%x"%x.tagno)
		f.write("\n")
	def write_free_func(self, f):
		f.write("/* Free func for %s */\n"%self)
	def write_decode_func(self, f):
		f.write("/* Decode func for %s */\n"%self)
	def __str__(self):
		return self.name
	def __iter__(self):
		return self._tags.__iter__()
	def __getitem__(self, idx):
		return self._tags[idx]
	def pretty_print(self):
		print "%s instance: %s"%(self.__class__.__name__,
					self.name)

		for (k, (n, x)) in self._tagmap.items():
			print "  Tag 0x%x: %s: %s"%(k, n, x.__class__.__name__)

		for (uname, arr) in self._unionmap.items():
			print "  Union %s contains:"%uname
			for (n, x) in arr:
				print "    - %s: %s"%(n, x.__class__.__name__)
		print "  Non-union tags:"
		for (n, x) in self._scab_tags:
			print "    - %s: %s"%(n, x.__class__.__name__)

		print
		for (n, x) in self._tags:
			if x.__class__ == CScalar:
				continue
			x.pretty_print()

class CStruct(CStructBase):
	def __init__(self, node, union = None):
		assert(node.__class__ == Template)
		assert(node.sequence == False)
		CStructBase.__init__(self, node.name, node.label, node.tag)
		self.union = union
		self._macro_prefix = self.name.upper() + "_"
		self._members(node.__iter__())

class CStructPtr(CStructBase):
	def __init__(self, node):
		assert(node.__class__ == Template)
		assert(node.sequence == True)
		CStructBase.__init__(self, node.name, node.label, node.tag)
		self._macro_prefix = self.name.upper() + "_"
		self._members(node.__iter__())
		self.union = None

class CRoot(CStructBase):
	def __init__(self, root):
		assert(root.__class__ == Root)
		assert(len(root) == 1)
		CStructBase.__init__(self, "root_", "Autober root node")
		self._macro_prefix = ''
		self._members(root.__iter__())

class CDefinitions:
	def write_tagblocks(self, f):
		self.root.write_tagblock(f)
		return

	def write_tag_macros(self, f):
		self.root.write_tag_macros(f)

	def write_free(self, f):
		self.root.write_free_func(f)

#	def __write_root_decode(self, f):
#		r = self.root
#		f.write("struct %s *%s_decode(const uint8_t *ptr, "\
#			"size_t len)\n"%(r, r))
#		f.write("{\n")
#		f.write("\tstruct %s *%s;\n\n"%(r, r))
#		f.write("\t%s = calloc(1, sizeof(*%s));\n"%(r, r))
#		f.write("\tif ( NULL == %s )\n"%r)
#		f.write("\t\treturn NULL;\n\n")
#
#		f.write("\tif ( !%s(%s, ptr, len) ) {\n"%(r.decode_func, r))
#		f.write("\t\t%s(%s);\n"%(r[0][1].free_func, r))
#		f.write("\t\treturn NULL;\n")
#		f.write("\t}\n\n")
#		f.write("\treturn %s;\n"%r)
#		f.write("}\n")

	def write_func_decls(self, f):
		r = self.root
		#f.write("struct %s *%s_decode(const uint8_t *ptr, "\
		#	"size_t len);\n"%(r, r))
		#f.write("void %s(struct %s *%s);\n"%(r.free_func, r, r))

	def write_decode(self, f):
		self.root.write_decode_func(f)

	def __init__(self, root):
		self.root = CRoot(root)
		self.root.pretty_print()
