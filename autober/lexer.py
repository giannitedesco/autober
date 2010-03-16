from tokens import *
from itertools import tee

class LexIter:
	def __init__(self, fn):
		self.filename = fn
		self.lineno = 0
		self.__linebuf = ''
		self.__charbuf = iter('')
		self.__hexmap = {}.fromkeys(
			[chr(ord('0') + i) for i in xrange(10)] +
			[chr(ord('a') + i) for i in xrange(6)] +
			[chr(ord('A') + i) for i in xrange(6)])
		self.__tokmap = {}.fromkeys(
			[chr(ord('0') + i) for i in xrange(10)] +
			[chr(ord('a') + i) for i in xrange(26)] +
			[chr(ord('A') + i) for i in xrange(26)] +
			['_'])

	def __get_line(self):
		self.lineno += 1
		line = self._input.next()
		if len(line) == 0:
			raise StopIteration
		assert(line[-1:] == '\n')
		if len(line) > 1 and line[:-2] == '\r':
			line = line[:-2] + '\n'
		self.__linebuf = line
		self.__charbuf = iter(line)

	def __get_char(self):
		try:
			return self.__charbuf.next()
		except StopIteration:
			self.__get_line()
			return self.__charbuf.next()

	def __ishex(self, char):
		assert(len(char) == 1)
		return self.__hexmap.has_key(char)
	def __istok(self, char):
		assert(len(char) == 1)
		return self.__tokmap.has_key(char)

	def __numtok(self, char):
		(self.__charbuf, it) = tee(self.__charbuf)
		while True:
			try:
				nchar = it.next()
			except StopIteration:
				raise Exception("Bad EOL")

			if len(char) == 1:
				hex = nchar == 'x'
				if hex:
					char += nchar
					self.__get_char()
					continue

			if hex:
				if not self.__ishex(nchar):
					break
			else:
				if not nchar.isdigit():
					break

			char += nchar
			self.__get_char()

		return LexInteger(self.filename, self.lineno, char)

	def __strtok(self, char):
		str = ''
		in_esc = False
		while True:
			nchar = self.__get_char()
			if not in_esc:
				if nchar == "\\":
					in_esc = True
					continue
				elif nchar == "'":
					break
			else:
				in_esc = False
			str += nchar
		return LexString(self.filename, self.lineno, str)

	def __regtok(self, char):
		(self.__charbuf, it) = tee(self.__charbuf)
		while True:
			try:
				nchar = it.next()
			except StopIteration:
				raise Exception("Bad EOL")
			if not self.__istok(nchar):
				break
			char += nchar
			self.__get_char()

		try:
			tok = LexKeyword(self.filename, self.lineno, char)
		except KeyError:
			try:
				tok = LexType(self.filename, self.lineno, char)
			except KeyError:
				tok = LexIdentifier(self.filename,
							self.lineno, char)
		return tok

	def __comment(self):
		star = self.__get_char()
		assert(star == '*')

		got_star = False
		while True:
			char = self.__get_char()
			if got_star and char == '/':
				return
			if char == '*':
				got_star = True
			else:
				got_star = False

	def __lex_one(self):
		charmap = {'{':LexOpenBrace,
			'}':LexCloseBrace,
			'[':LexOpenSub,
			']':LexCloseSub,
			';':LexSemiColon,
			'-':LexRange,
		}

		char = self.__get_char()
		while char.isspace():
			char = self.__get_char()
		if charmap.has_key(char):
			return charmap[char](self.filename, self.lineno)

		if char == '/':
			self.__comment()
			return

		if char.isdigit():
			return self.__numtok(char)
		elif self.__istok(char):
			return self.__regtok(char)

		if char == "'":
			return self.__strtok(char)

		assert(char.isspace())

	def next(self):
		tok = None
		while not tok:
			tok = self.__lex_one()
		return tok

class LexIterFile(LexIter):
	def __init__(self, filename):
		LexIter.__init__(self, filename)
		self.__file = open(filename)
		self._input = self.__file.__iter__()

class LexIterString(LexIter):
	def __init__(self, str):
		LexIter.__init__(self, object.__repr__(str))
		# ffs, split :(
		self._input = map(lambda x:x + '\n', str.split('\n'))

class lexer:
	def __iter__(self):
		# TODO: preprocessing and string pasting
		return self.__lex

	def __init__(self, file):
		self.__lex = LexIterFile(file)
