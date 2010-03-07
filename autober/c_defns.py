from syntax import *

class CDefinition:
	def __scalar(self, root, prefix = ''):
		ret = []
		for x in root:
			name = prefix + "." + x.name
			if Fixed in x.__class__.__bases__:
				ret.append((name, x))
			elif x.__class__ == Template and not x.sequence:
				ret.extend(self.__scalar(x, name))
			elif x.__class__ == Union:
				ret.extend(self.__scalar(x, name))
		return ret

	def __ptrs(self, root):
		ret = []
		for x in root:
			name = "->" + x.name
			if x.__class__ == Template and x.sequence:
				ret.append((name, x, CDefinition(x)))
		return ret

	def __iter__(self):
		return self.ptrs.__iter__()
	def __getitem__(self, idx):
		return self.ptrs[idx]

	def __str__(self):
		return self.name

	def __init__(self, root):
		self.name = root.name
		self.scalar = self.__scalar(root)
		self.ptrs = self.__ptrs(root)

class CDefinitions:
	def __do_print(self, node, depth = 0):
		indent = ''.join("\t" for x in range(depth))
		for (n, x) in node.scalar:
			print "%s%s"%(indent, n)
		for (n, x, d) in node:
			print "%s%s"%(indent, n)
			self.__do_print(d, depth + 1)
			
	def pretty_print(self):
		print str(self.root)
		self.__do_print(self.root, 1)

	def __do_free(self, f, node, path):
		for (n, x, d) in node:
			self.__do_free(f, d, d.name)

		f.write("static void _free_%s(struct *%s %s)\n"%(str(node),
							str(node),
							str(node)))
		f.write("{\n")
		f.write("\tif ( %s ) {\n"%str(node))
		for (n, x, d) in node:
			f.write("\t\tfree_%s(%s)\n"%(d.name, path + n))

		for (n, x) in node.scalar:
			if x.__class__ == Blob:
				f.write("\t\tfree(%s.ptr)\n"%(path + n))
		f.write("\t}\n")
		f.write("\tfree(%s)\n"%(path))
		f.write("}\n\n")

	def write_free(self, f):
		self.__do_free(f, self.root, str(self.root))
		f.write("void free_%s(struct %s *%s)\n"%(str(self.root),
							str(self.root),
							str(self.root)))
		f.write("{\n")
		f.write("\t_free_%s(%s)\n"%(str(self.root), str(self.root)))
		f.write("}\n")

	def __init__(self, root):
		self.root = CDefinition(root)
		self.pretty_print()
