class lexer:
	def __top(self):
		if not len(self.__toks):
			return None
		[ret] = self.__toks[-1:]
		return ret

	def __paste(self, tok):
		x = self.__toks.pop()
		self.__toks.append(x[:-1] + tok)

	def __append(self, tok):
		if tok[-1:] == ';':
			self.__toks.append(tok[:-1])
			self.__toks.append(";")
		else:
			self.__toks.append(tok)

	def __extend(self, list):
		for tok in list:
			self.__append(tok)

	def __qsplit(self, str):
		"Tokenize a line of netscreen config."

		# Standard whitespace split allowing for quote marks but no
		# escape chars from within quotemarks
		inq = False
		for sub in str.split("'"):
			y = self.__top()
			if y and y[-1:] == "\\":
				self.__paste("'" + sub)
				continue

			if not inq:
				self.__extend(sub.split())
			else:
				self.__append(sub)

			inq = not inq

	def __iter__(self):
		return self.__toks.__iter__()

	def __init__(self, file):
		lines = file.readlines()
		lines = map(lambda x:x.rstrip('\r\n'), lines)
		self.__toks = []
		for l in lines:
			self.__qsplit(l)
		return
