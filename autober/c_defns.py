from syntax import *

class CDefn:
	pass
class CContainer:
	pass
class CUnion(CDefn,CContainer):
	pass
class CScalar(CDefn):
	def __init__(self, node):
		self.name = node.name
		if node.__class__ == Blob:
			self.is_blob = True
		else:
			self.is_blob = False
	def write_free(self, f, name, indent = 1):
		if not self.is_blob:
			return
		f.write("%sfree(%s.ptr);\n"%(\
			''.join("\t" for i in range(indent)),
			name))

class CStructPtr(CDefn,CContainer):
	def __scalar(self, node, prefix = ''):
		ret = []
		for x in node:
			name = prefix + "." + x.name
			if Fixed in x.__class__.__bases__:
				ret.append((name, CScalar(x)))
			elif x.__class__ == Template and not x.sequence:
				ret.extend(self.__scalar(x, name))
		return ret

	def __ptrs(self, node):
		ret = []
		for x in node:
			name = "->" + x.name
			if x.__class__ == Template and x.sequence:
				ret.append((name, CStructPtr(x)))
		return ret

	def __str__(self):
		return self.name

	def __init__(self, node, root = False):
		self.is_root = root
		if not root:
			self.count_var = "._%s_count"%node.name
		self.name = node.name
		self.scalar = self.__scalar(node)
		self.ptrs = self.__ptrs(node)
	
	def write_free(self, f):
		for (n, x) in self.ptrs:
			x.write_free(f)
		f.write("static void _free_%s(struct %s *%s)\n"%(str(self),
								str(self),
								str(self)))
		f.write("{\n")
		if len(self.ptrs):
			f.write("\tunsigned int i;\n\n");
		if self.is_root:
			f.write("\tif ( NULL == %s )\n"%str(self))
			f.write("\t\treturn;\n\n")
		for (n, x) in self.ptrs:
			f.write("\tfor(i = 0; i < %s%s; i++)\n"%(
						str(self), x.count_var))
			f.write("\t\t_free_%s(%s%s);\n"%(str(x),
							str(self), n))
			f.write("\tfree(%s%s);\n\n"%(str(self), n))
		for (n, x) in self.scalar:
			x.write_free(f, "%s%s"%(str(self), n))
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
			
	def pretty_print(self):
		print str(self.root)
		self.__do_print(self.root, 1)

	def write_free(self, f):
		self.root.write_free(f)
		f.write("void free_%s(struct %s *%s)\n"%(str(self.root),
							str(self.root),
							str(self.root)))
		f.write("{\n")
		f.write("\t_free_%s(%s);\n"%(str(self.root), str(self.root)))
		f.write("}\n")

	def __init__(self, root):
		self.root = CStructPtr(root, root=True)
		self.pretty_print()
