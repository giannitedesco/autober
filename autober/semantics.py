from parser import Root, Template, Union, Fixed

class semantics:
	def __do_symbol_map(self, map, node):
		for x in node:
			if map.has_key(x.name):
				raise Exception("Symbol '%s' multiply defined"%(
					x.name))
			map[x.name] = x
			if x.__class__ != Fixed:	
				self.__do_symbol_map(map, x)

	def __symbol_map(self, root):
		map = {}
		for x in root:
			self.__do_symbol_map(map, x)
		return map

	def __init__(self, root):
		map = self.__symbol_map(root)
		return
