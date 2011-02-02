from syntax import *

CPP_TAG_SUFFIX		= '_TAG'
CPP_PRESENCE_SUFFIX	= ''
CPP_TYPE_INFIX		= '_TYPE_'

C_TAGBLOCK_SUFFIX	= '_tags'
C_DECODE_FUNC_SUFFIX	= '_decode'
C_FREE_FUNC_SUFFIX	= '_free'

def preproc_define(f, name, val):
	f.write('#define %-30s %s\n'%(name, val))

class CTagStruct:
	def __init__(self, label, cpptag, union = False, optional = False):
		self.label = label
		self.cpptag = cpptag
		self.union = union
		self.optional = optional
		self.check_size = False

		self.template = None

	def flags(self):
		list = []
		if self.template:
			list.append('AUTOBER_TEMPLATE')
			if self.sequence:
				list.append('AUTOBER_SEQUENCE')
		if self.union:
			list.append('AUTOBER_UNION')
		if self.optional:
			list.append('AUTOBER_OPTIONAL')
		if self.check_size:
			list.append('AUTOBER_CHECK_SIZE')
		return '|'.join(list)

	def set_template(self, sequence = False):
		self.template = True
		self.sequence = False

	def set_sizes(self, min, max):
		self.check_size = True
		assert(min <= max)
		self.constraint = (min, max)

	def write(self, f):
		f.write('\t{.ab_label = "%s",\n'%self.label)
		if self.flags() != '':
			f.write('\t\t.ab_flags = %s,\n'%self.flags())
		if self.check_size:
			f.write('\t\t.ab_size = {%u, %u},\n'%self.constraint)
		f.write('\t\t.ab_tag = %s},\n'%self.cpptag)

class CScalar:
	def __init__(self, node, union = None):
		self.union = union
		self.tagno = node.tag
		self.name = node.name
		self.label = node.name
		self.constraint = node.constraint
		self.optional = node.optional
		self.need_free = False
		if isinstance(node, Blob):
			self.need_free = True
			self.dfunc = 'autober_blob(%(var)s, &tag, ptr)'
		elif isinstance(node, Uint):
			self.dfunc = 'autober_u%d(%%(var)s, &tag, ' \
					'ptr, %%(countvar)s)'%\
					node.bits
		else:
			assert(False)

		if node.constraint is not None:
			self.array_sz = node.constraint[1] / node.bytes
			if self.array_sz == 1:
				self.array_sz = 0
		else:
			self.array_sz = 0

	def set_count_var(self, cname):
		self.count_var = cname
	def set_cname(self, name):
		self.cname = name
	def set_cppname(self, name):
		self.cppname = name
	def set_typename(self, name):
		if not name == None:
			self.typename = name
	def set_optvar(self, name):
		if self.optional:
			self.optvar = name
	def call_decode(self, var, countvar = None):
		if countvar is None:
			countvar = 'NULL'
		d = {'var':var, 'countvar':countvar}
		return self.dfunc%d
	def call_free(self, f, indent = 1):
		tabs = ''.join('\t' for i in xrange(indent))
		if self.need_free:
			f.write(tabs + 'free(%s.ptr);\n'%(self.cname))

class CStructBase:
	def __init__(self, name, label, tagno = None, optional = False):
		self.name = name
		self.label = label
		self.tagno = tagno
		self.prefix = '->'
		self.tagblock_name = '%s%s'%(self.name, C_TAGBLOCK_SUFFIX)
		self.free_func = '_free_%s'%(self.name)
		self.decode_func = '_%s'%(self.name)
		self.optional = optional

	def set_count_var(self, cname):
		self.count_var = cname

	def set_cname(self, name):
		self.cname = name
	def set_cppname(self, name):
		self.cppname = name
	def set_optvar(self, name):
		if self.optional:
			self.optvar = name
	def set_typename(self, name):
		if not name == None:
			self.typename = name

	def __recurse(self, node, union = None):
		if isinstance(node, Template):
			if node.sequence:
				assert(union == None)
				memb = CStructPtr(node)
			else:
				memb = CStruct(node, union)
		else:
			memb = CScalar(node, union)
		return memb

	def _name_union(self, u):
		un = '%s%s%s'%(self.name, self.prefix, u.name)
		ut = '%s%s_%s_type'%(self.name, self.prefix, u.name)
		return (un, ut)

	def _name_member(self, ch):
		if ch.union:
			return '%s%s%s.%s'%(self.name, self.prefix,
						ch.union.name, ch.name)
		else:
			return '%s%s%s'%(self.name, self.prefix, ch.name)

	def _name_optvar(self, ch):
		return '%s%s%s'%(self.name, self.prefix, '_present')

	def _name_count_var(self, ch):
		return '%s%s_%s_count'%(self.name, self.prefix, ch.name)

	def _name_macro(self, ch):
		if ch.union:
			return '%s%s_%s'%(self._macro_prefix,
						ch.union.name.upper(),
						ch.name.upper())
		else:
			return '%s%s'%(self._macro_prefix, ch.name.upper())
	
	def _name_union_member(self, ch):
		if ch.union:
			return '%s_%s%s%s'%(self.name.upper(),
					ch.union.name.upper(),
					CPP_TYPE_INFIX,
					ch.name.upper())
		else:
			return None

	def _members(self, iter):
		m = []
		for x in iter:
			if isinstance(x, Union):
				for y in x:
					memb = self.__recurse(y, union = x)
					m.append(memb)
			else:
				memb = self.__recurse(x)
				m.append(memb)

		map(lambda x:x.set_cname(self._name_member(x)), m)
		map(lambda x:x.set_cppname(self._name_macro(x)), m)
		map(lambda x:x.set_typename(self._name_union_member(x)), m)
		map(lambda x:x.set_optvar(self._name_optvar(x)), m)
		self._tags = m

		self._tagmap = {}
		for x in self._tags:
			self._tagmap[x.tagno] = x

		self._scab_tags = filter(lambda x:not x.union, self._tags)

		self._sequences = filter(lambda x:isinstance(x, CStructPtr),
					self._scab_tags)
		for seq in self._tags:
			seq.set_count_var(self._name_count_var(seq))

		utags = filter(lambda x:x.union, self._tags)
		self._unionmap = {}
		for x in utags:
			uname = self._name_union(x.union)
			if not self._unionmap.has_key(uname):
				self._unionmap[uname] = []
			self._unionmap[uname].append(x)

	def write_tagblock(self, f):
		for x in self._tags:
			if isinstance(x, CScalar):
				continue
			x.write_tagblock(f)

		f.write('/* Tags for %s */\n'%self)
		f.write('static const struct autober_tag %s[] = {\n'%
			self.tagblock_name)
		for x in self._tags:
			tagstruct = CTagStruct(x.label,
						x.cppname + CPP_TAG_SUFFIX,
						x.union != None,
						x.optional)
			if isinstance(x, CStruct):
				tagstruct.set_template(sequence = False)
			elif isinstance(x, CStructPtr):
				tagstruct.set_template(sequence = True)
			elif x.constraint != None:
				tagstruct.set_sizes(*x.constraint)
			tagstruct.write(f)
		f.write('};\n\n')

	def write_tag_macros(self, f):
		for x in self._tags:
			if isinstance(x, CScalar):
				continue
			x.write_tag_macros(f)
		f.write('/* Tag numbers for %s */\n'%self)
		for x in self._tags:
			preproc_define(f, x.cppname + CPP_TAG_SUFFIX,
					'0x%x'%x.tagno)
		f.write('\n')

	def __union_free(self, f, un, ut, arr):
		f.write('\tswitch(%s) {\n'%(ut))
		for x in arr:
			f.write('\tcase %s:\n'%x.typename)
			x.call_free(f, indent = 2)
			f.write('\t\tbreak;\n')
		f.write('\t}\n')

	def write_free_func(self, f, check_null = False):
		for x in self._tags:
			if isinstance(x, CScalar):
				continue
			x.write_free_func(f)

		f.write('/* Free func for %s */\n'%self)
		f.write('static void %s(struct %s *%s)\n'%(
			self.free_func, self.name, self.name))
		f.write('{\n')

		if len(self._sequences):
			f.write('\tunsigned int i;\n\n');

		if check_null:
			f.write('\tif ( NULL == %s )\n'%str(self))
			f.write('\t\treturn;\n\n')

		for x in self._sequences:
			f.write('\tfor(i = 0; i < %s; i++)\n'%(
						x.count_var))
			x.call_free(f, indent = 2)
			f.write('\tfree(%s);\n'%x.cname)

		for ((un, ut), arr) in self._unionmap.items():
			self.__union_free(f, un, ut, arr)
		for x in self._scab_tags:
			if x in self._sequences:
				continue
			if x.optional:
				f.write('\tif ( %s & %s) {\n'%(x.optvar,
								x.cppname))
				x.call_free(f, indent = 2)
				f.write('\t}\n')
			else:
				x.call_free(f)

		if check_null:
			f.write('\tfree(%s);\n'%self.cname)
		f.write('}\n')
		f.write('\n')

	def call_decode(self, var, countvar = None):
		return '_%s_decode(%s, ptr, tag.ber_len)'%(
			self.name, var)

	def write_decode_func(self, f):
		for x in self._tags:
			if isinstance(x, CScalar):
				continue
			x.write_decode_func(f)
		f.write('/* Decode func for %s */\n'%self.name)
		f.write('static int _%s_decode(struct %s *%s,\n'%(self.name,
								self.name,
								self.name))
		f.write('\t\t\tconst uint8_t *ptr, size_t len)\n')
		f.write('{\n')
		f.write('\tstatic const unsigned int num = '
			'AUTOBER_NUM_TAGS(%s_tags);\n'%self.name)
		f.write('\tstruct autober_constraint cons[num];\n')
		f.write('\tstruct gber_tag tag;\n')
		f.write('\tconst uint8_t *end;\n')
		f.write('\n')
		f.write('\tif ( !autober_constraints(%s_tags, cons, '
			'num, ptr, len) ) {\n'%self.name)
		f.write('\t\tfprintf(stderr, "%s: '
			'constraints not satisified\\n");\n'%self.name)
		f.write('\t\treturn 0;\n')
		f.write('\t}\n')
		f.write('\n')

		f.write('\tfor(end = ptr + len; ptr < end; '
			'ptr += tag.ber_len) {\n')
		f.write('\t\tptr = ber_decode_tag(&tag, ptr, end - ptr);\n')
		f.write('\t\tif ( NULL == ptr )\n')
		f.write('\t\t\treturn 0;\n')
		f.write('\n')
		f.write('\t\tswitch(tag.ber_tag) {\n')
		for x in self._tags:
			f.write('\t\tcase %s:\n'%(x.cppname + CPP_TAG_SUFFIX))
			cv = None
			if isinstance(x, CStructPtr):
				var = '&%s[%s]'%(x.cname,
							x.count_var)
			elif isinstance(x, CScalar) and x.array_sz:
				if x.constraint[0] != x.constraint[1]:
					cv = '&' + x.count_var
				var = '%s'%x.cname
			else:
				var = '&%s'%x.cname
			f.write('\t\t\tif ( !%s )\n'%x.call_decode(var, cv))
			f.write('\t\t\t\treturn 0;')
			f.write('\n')
			if isinstance(x, CStructPtr):
				f.write('\t\t\t%s++;\n'%x.count_var)
			if x.optional:
				f.write('\t\t\t%s |= %s;\n'%(
					x.optvar, x.cppname))
			if x.union:
				(un,ut) = self._name_union(x.union)
				f.write('\t\t\t%s = %s;\n'%(ut, x.typename))
			f.write('\t\t\tbreak;\n')
		f.write('\t\tdefault:\n')
		f.write('\t\t\tfprintf(stderr, "Unexpected tag: '
			'%s: 0x%%x\\n",\n'
			'\t\t\t\ttag.ber_tag);\n'%self.name)
		f.write('\t\t\tcontinue;\n')
		f.write('\t\t}\n')
		f.write('\t}\n')
		f.write('\treturn 1;\n')
		f.write('}\n')
		f.write('\n')

	def __str__(self):
		return self.name

	def __iter__(self):
		return self._tags.__iter__()

	def __getitem__(self, idx):
		return self._tags[idx]

	def pretty_print(self):
		for x in self._tags:
			if isinstance(x, CScalar):
				continue
			x.pretty_print()

		print
		print '%s instance: %s'%(self.__class__.__name__,
					self.name)
		print 'Free func: %s'%self.free_func
		print 'Decode func: %s'%self.decode_func

		for (k, x) in self._tagmap.items():
			print '  Tag 0x%x: %s / %s: %s'%(k, x.cname,
						x.cppname,
						x.__class__.__name__)

		for ((un, ut), arr) in self._unionmap.items():
			print '  Union %s / %s contains:'%(un, ut)
			for x in arr:
				print '    - [%s] %s: %s'%(x.typename,
							x.cname,
							x.__class__.__name__)
		print '  Non-union tags:'
		for x in self._scab_tags:
			if x.optional:
				print '    - %s: %s selected by %s'%(x.cname,
							x.__class__.__name__,
							x.cppname)
			else:
				print '    - %s: %s'%(x.cname,
							x.__class__.__name__)

class CStruct(CStructBase):
	def call_free(self, f, indent = 1):
		tabs = ''.join('\t' for i in xrange(indent))
		f.write(tabs + '%s(&%s);\n'%(self.free_func, self.cname))

	def __init__(self, node, union = None):
		assert(isinstance(node, Template))
		assert(node.sequence == False)
		CStructBase.__init__(self, node.name, node.label,
					node.tag, node.optional)
		self.union = union
		self._macro_prefix = self.name.upper() + '_'
		self._members(node.__iter__())

class CStructPtr(CStructBase):
	def call_free(self, f, indent = 1):
		tabs = ''.join('\t' for i in xrange(indent))
		f.write(tabs + '%s(&%s[i]);\n'%(self.free_func, self.cname))

	def __init__(self, node):
		assert(isinstance(node, Template))
		assert(node.sequence == True)
		CStructBase.__init__(self, node.name, node.label,
					node.tag, node.optional)
		self._macro_prefix = self.name.upper() + '_'
		self._members(node.__iter__())
		self.union = None

class CRoot(CStructBase):
	def __init__(self, root, modname):
		assert(root.__class__ == Root)
		assert(len(root) == 1)
		CStructBase.__init__(self, root[0].name, 'Autober root node')
		self.tagblock_name = 'root_' + self.tagblock_name
		self._macro_prefix = ''
		self.prefix = ''
		self._members(root.__iter__())

	def _name_union(self, u):
		return (u.name, '_%s_type'%u.name)

	def _name_member(self, ch):
		if ch.union:
			return '%s.%s'%(ch.union.name, ch.name)
		else:
			return ch.name

	def write_free_func(self, f):
		root = self._tags[0]
		root.write_free_func(f, check_null = True)
		f.write('/* Free func for %s module */\n'%root.cname)
		f.write('void %s%s(struct %s *%s)\n'%(root.cname,
			C_FREE_FUNC_SUFFIX, root.cname, root.cname))
		f.write('{\n')
		f.write('\t%s(%s);\n'%(root.free_func, root.cname))
		f.write('}\n')
		f.write('\n')

	def write_decode_func(self, f):
		root = self._tags[0]

		CStructBase.write_decode_func(root, f)

		f.write('/* Decode func for %s module */\n'%root.cname)
		f.write('struct %s *%s%s(const uint8_t *ptr, size_t len)\n'%(
			root.cname, root.cname, C_DECODE_FUNC_SUFFIX))
		f.write('{\n')
		f.write('\tstruct %s *%s;\n'%(root.cname, root.cname))
		f.write('\n')
		f.write('\t%s = calloc(1, sizeof(*%s));\n'%(
			root.cname, root.cname))
		f.write('\tif ( NULL == %s )\n'%root.cname)
		f.write('\t\treturn NULL;\n')
		f.write('\n')
		f.write('\tif ( !_%s_decode(%s, ptr, len) ) {\n'%(
			root.cname, root.name))
		f.write('\t\t_free_%s(%s);\n'%(root.name,root.cname))
		f.write('\t\treturn NULL;\n')
		f.write('\t}\n')
		f.write('\n')
		f.write('\treturn %s;\n'%root.cname)
		f.write('}\n')

	def write_func_decls(self, f):
		root = self._tags[0]
		f.write('struct %s *%s%s(const uint8_t *ptr, size_t len);\n'%(
			root.cname, root.cname, C_DECODE_FUNC_SUFFIX))
		f.write('void %s%s(struct %s *%s);\n'%(root.cname,
			C_FREE_FUNC_SUFFIX, root.cname, root.cname))

class CDefinitions:
	def write_tagblocks(self, f):
		self.root.write_tagblock(f)
		return

	def write_tag_macros(self, f):
		self.root.write_tag_macros(f)

	def write_free(self, f):
		self.root.write_free_func(f)

	def write_func_decls(self, f):
		self.root.write_func_decls(f)

	def write_decode(self, f):
		self.root.write_decode_func(f)

	def __init__(self, root, modname):
		self.root = CRoot(root, modname)
		self.root.pretty_print()
