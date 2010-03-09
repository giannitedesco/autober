from syntax import *

class CDefn:
	pass
class CScalar(CDefn):
	def __init__(self, node):
		self.name = node.name
		if node.__class__ == Blob:
			self.is_blob = True
		else:
			self.is_blob = False
	def call_free(self, f, name, indent = 1):
		if not self.is_blob:
			return
		f.write("%sfree(%s.ptr);\n"%(\
			''.join("\t" for i in range(indent)),
			name))

class CContainer:
	def __scalar(self, node, prefix = '', toplevel = False):
		ret = []
		for x in node:
			if toplevel:
				name = prefix + self.prefix + x.name
			else:
				name = prefix + '.' + x.name
			if Fixed in x.__class__.__bases__:
				r = [(name, CScalar(x))]
			elif x.__class__ == Template and not x.sequence:
				r = self.__scalar(x, prefix = name)
			else:
				continue
			ret.extend(r)
			self.toplevel.extend(r)
		return ret

	def __ptrs(self, node):
		ret = []
		for x in node:
			name = self.prefix + x.name
			if x.__class__ != Template:
				continue
			if x.sequence:
				ret.append((name, CStructPtr(x)))
			else:
				ret.extend(self.__ptrs(x))
		return ret

	def __unions(self, node):
		ret = []
		for x in node:
			if x.__class__ != Union:
				continue
			name = self.prefix + x.name
			ret.append((name, CUnion(self, x)))
		return ret

	def __str__(self):
		return self.name

	def __init__(self, node, prefix = '.', root = False):
		self.is_root = root
		self.prefix = prefix
		if not root:
			self.count_var = "%s_%s_count"%(self.prefix, node.name)
		self.name = node.name
		self.toplevel = []
		self.scalar = self.__scalar(node, toplevel = True)
		self.ptrs = self.__ptrs(node)
		self.unions = self.__unions(node)
		self.toplevel.extend(self.ptrs)
		self.toplevel.extend(self.ptrs)

class CUnion(CDefn,CContainer):
	def __init__(self, parent, node, prefix = '.'):
		CContainer.__init__(self, node, root = False)
		self.type_var = "%s_%s_type"%(parent.prefix, node.name)
		self.choices = {}
		for (n, x) in self.toplevel:
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
			x.call_free(f, str(parent) + name + n,
					indent = indent + 1)
			f.write("%s\tbreak;\n"%tabs)
		f.write("%s}\n"%tabs);
		return

class CStructPtr(CDefn,CContainer):
	def __init__(self, node, root = False):
		CContainer.__init__(self, node, prefix = '->', root = root)

	def call_free(self, f, name, indent = 1):
		tabs = ''.join("\t" for i in range(indent))
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
			#f.write("\t\t_free_%s(&%s%s[i]);\n"%(str(x),
			#				str(self), n))
			x.call_free(f, "%s%s"%(str(self), n), indent = 2)
			f.write("\tfree(%s%s);\n\n"%(str(self), n))

		for (n, x) in self.unions:
			x.write_free(f, str(self), n)
		for (n, x) in self.scalar:
			x.call_free(f, "%s%s"%(str(self), n))

		if self.is_root:
			f.write("\tfree(%s);\n"%str(self))
		f.write("}\n\n")

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
		f.write("}\n")

	def __init__(self, root):
		self.root = CStructPtr(root, root=True)
		self.pretty_print()
