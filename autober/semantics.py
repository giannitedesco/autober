from parser import Root, Template, Union, Fixed

class semantics:
	def __tmplsym_map(self):
		ret = {}
		for x in self.nodes:
			if x.__class__ != Template:
				continue
			if ret.has_key(x.name):
				raise Exception("Template name '%s' "
						"multiply defined"%(x.name))
			ret[x.name] = x

		return ret

	def __do_flatten(self, list, node):
		for x in node:
			list.append(x)
			self.__do_flatten(list, x)

	def __flatten(self, root):
		list = []
		self.__do_flatten(list, root)
		return list

	def __check_unions(self):
		for u in self.nodes:
			if u.__class__ != Union:
				continue
			utags = {}
			ptags = {}
			for ue in u:
				utags[ue.tag] = None
			for pe in u.parent:
				if pe == u:
					continue
				ptags[pe.tag] = None

			us = set(utags.keys())
			ps = set(ptags.keys())
			if len(us & ps):
				raise Exception("%s: Union tags intersect "
						"with parent: %s"%(u.name,
								us & ps))

	def __init__(self, root):
		self.parse_tree = root
		self.nodes = self.__flatten(root)

		# 2. Check template names not multiply defined
		self.templates = self.__tmplsym_map()

		# 2. Check union tags don't conflict with parent template
		self.unions = self.__check_unions()

		# 3. Check variable names valid C tokens

		return
