class AutoberException:
	LINE_UNKNOWN = 0
	def __init__(self, type, explanation, filename = None, lineno = 0):
		self.type = str(type)
		self.filename = filename
		self.lineno = lineno
		self.explanation = explanation
	def __str__(self):
		if self.filename or self.lineno:
			loc = "%s:%u: "%(self.filename, self.lineno)
		else:
			loc = ''
		return "%s%s: %s"%(loc, self.type, self.explanation)

class ParseError(AutoberException):
	def __init__(self, filename, lineno, explanation):
		AutoberException.__init__(self, "Parse Error", explanation,
					filename, lineno)

class BadSyntax(AutoberException):
	def __init__(self, tok, explanation, extra = True):
		if extra:
			ext = ": near token '%s'"%str(tok)
		else:
			ext = ''
		AutoberException.__init__(self, "Syntax Error",
					explanation + ext,
					tok.filename, tok.lineno)
