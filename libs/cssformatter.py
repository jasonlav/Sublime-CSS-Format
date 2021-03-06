#!/usr/bin/python
# encoding: utf-8
#
# Convert CSS/SASS/SCSS/LESS code to Expanded, Compact or Compressed format.
#
# Usage: format_css(code, action)
# Author: Mutian Wang <mutian@me.com>
#

import re


def format_css(code, action='compact', indentation='\t', rule_break='\n'):
	actFuns = {
		'expand'		: expand_rules,
		'expand-bs'		: expand_rules,			# expand (break selectors)
		'compact'		: compact_rules,
		'compact-bs'	: compact_rules,		# compact (break selectors)
		'compact-ns'	: compact_ns_rules,		# compact (no spaces)
		'compact-bs-ns'	: compact_ns_rules,		# compact (break selectors, no spaces)
		'compress'		: compress_rules
	}

	if action not in actFuns:
		return code

	# Comments
	if action == 'compress':
		# remove comments
		code = re.sub(r'\s*\/\*[\s\S]*?\*\/\s*', '', code)
	else:
		# Protect Comments
		commentReg = r'[ \t]*\/\*[\s\S]*?\*\/'
		comments = re.findall(commentReg, code)
		code = re.sub(commentReg, '!comment!', code)

	# Protect Strings
	stringReg = r'(content\s*:|[\w-]+\s*=)\s*(([\'\"]).*?\3)\s*'
	strings = re.findall(stringReg, code)
	code = re.sub(stringReg, r'\1!string!', code)

	# Protect Urls
	urlReg = r'((?:url|url-prefix|regexp)\([^\)]+\))'
	urls = re.findall(urlReg, code)
	code = re.sub(urlReg, '!url!', code)

	# Pre Process
	code = re.sub(r'\s*([\{\}:;,])\s*', r'\1', code)	# remove \s before and after characters {}:;,
	code = re.sub(r'([\[\(])\s*', r'\1', code)			# remove space inner [ or (
	code = re.sub(r'\s*([\)\]])', r'\1', code)			# remove space inner ) or ]
	# code = re.sub(r'(\S+)\s*([\+>~])\s*(\S+)', r'\1\2\3', code)	# remove \s before and after relationship selectors
	code = re.sub(r',[\d\s\.\#\+>~:]*\{', '{', code)	# remove invalid selectors without \w
	code = re.sub(r'([;,])\1+', r'\1', code)			# remove repeated ;,

	if action != 'compress':
		# group selector
		if re.search('-bs', action):
			code = break_selectors(code)				# break after selectors' ,
		else:
			code = re.sub(r',\s*', ', ', code)			# add space after ,

		# add space
		if re.search('-ns', action):
			code = re.sub(r', +', ',', code)								# remove space after ,
			code = re.sub(r'\s+!important', '!important', code)				# remove space before !important
		else:
			code = re.sub(r'([A-Za-z-]):([^;\{]+[;\}])', r'\1: \2', code)	# add space after properties' :
			code = re.sub(r'\s*!important', ' !important', code)			# add space before !important

	# Process Action Rules
	code = actFuns[action](code, rule_break)


	if action == 'compress':
		# remove last semicolon
		code = code.replace(';}', '}')
	else:
		# Fix Comments
		code = re.sub(r'\s*!comment!\s*@', '\n\n!comment!\n@', code)
		code = re.sub(r'\s*!comment!\s*([^\/\{\};]+?)\{', r'\n\n!comment!\n\1{', code)
		code = re.sub(r'\s*\n!comment!', '\n\n!comment!', code)

		# Backfill Comments
		for i in range(len(comments)):
			code = re.sub(r'[ \t]*!comment!', comments[i], code, 1)

		# Indent
		code = indent_code(code, indentation)

	# Backfill Strings
	for i in range(len(strings)):
		code = code.replace('!string!', strings[i][1], 1)

	# Backfill Urls
	for i in range(len(urls)):
		code = code.replace('!url!', urls[i], 1)

	# Trim
	code = re.sub(r'^\s*(\S+(\s+\S+)*)\s*$', r'\1', code)

	return code


# Expand Rules
def expand_rules(code, rule_break):
	code = re.sub('{', ' {\n', code)									# add space before { and add \n after {

	code = re.sub(';', ';\n', code)										# add \n after ;
	code = re.sub(r';\s*([^\{\};]+?)\{', r';\n\n\1{', code)				# double \n between ; and include selector

	code = re.sub(r'\s*(!comment!)\s*;\s*', r' \1 ;\n', code)			# fix comment before ;
	code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1 \2\n', code)		# fix comment after ;

	code = re.sub(r'\s*\}', '\n}', code)								# add \n before }
	code = re.sub(r'\}\s*', '}'+rule_break, code)								# add \n after }

	return code


# Compact Rules
def compact_rules(code):
	code = re.sub('{', ' { ', code)											# add space before and after {
	code = re.sub(r'(@[\w-]*(document|font-feature-values|keyframes|media|supports)[^;]*?\{)\s*', r'\1\n', code)
																			# add \n after @xxx {

	code = re.sub(';', '; ', code)											# add space after ;
	code = re.sub(r'(@(charset|import|namespace).+?;)\s*', r'\1\n', code)	# add \n after @charset & @import
	code = re.sub(r';\s*([^\};]+?\{)', r';\n\1', code)						# add \n before included selector

	code = re.sub(r'\s*(!comment!)\s*;', r' \1 ;', code)					# fix comment before ;
	code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1 \2 ', code)			# fix comment after ;

	code = re.sub(r'\s*\}', ' }', code)										# add space before }
	code = re.sub(r'\}\s*', '}\n', code)									# add \n after }

	return code


# Compact Rules (no space)
def compact_ns_rules(code):
	code = re.sub(r'(@[\w-]*(document|font-feature-values|keyframes|media|supports)[^;]*?\{)\s*', r'\1\n', code)
																			# add \n after @xxx {

	code = re.sub(r'(@(charset|import|namespace).+?;)\s*', r'\1\n', code)	# add \n after @charset & @import
	code = re.sub(r';\s*([^\};]+?\{)', r';\n\1', code)						# add \n before included selector

	code = re.sub(r'\s*(!comment!)\s*;', r'\1;', code)						# fix comment before ;
	code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1\2', code)			# fix comment after ;

	code = re.sub(r'\}\s*', '}\n', code)									# add \n after }

	return code


# Compress Rules
def compress_rules(code):
	code = re.sub(r'\s*([\{\}:;,])\s*', r'\1', code)					# remove \s before and after characters {}:;, again
	code = re.sub(r'\s+!important', '!important', code)					# remove space before !important
	code = re.sub(r'((?:@charset|@import)[^;]+;)\s*', r'\1\n', code)	# add \n after @charset & @import

	return code


# Break after Selector
def break_selectors(code):
	block = code.split('}')
	for i in range(len(block)):

		b = block[i].split('{')
		bLen = len(b)
		for j in range(bLen):

			if j == bLen - 1:
				b[j] = re.sub(r',\s*', ', ', b[j])			# add space after properties' ,
			else:
				s = b[j].split(';')
				sLen = len(s)
				sLast = s[sLen - 1]

				for k in range(sLen - 1):
					s[k] = re.sub(r',\s*', ', ', s[k])		# add space after properties' ,

				if re.match(r'\s*@(document|media)', sLast):
					s[sLen - 1] = re.sub(r',\s*', ', ', sLast)		# add space after @media's ,
				else:
					s[sLen - 1] = re.sub(r',\s*', ',\n', sLast)		# add \n after selectors' ,

				b[j] = ';'.join(s)

		block[i] = '{'.join(b)

	code = '}'.join(block)

	return code


# Code Indent
def indent_code(code, indentation='\t'):
	lines = code.split('\n')
	level = 0
	inComment = False
	outPrefix = ''

	for i in range(len(lines)):
		adjustment = lines[i].count('{') - lines[i].count('}')
		nextLevel = level + adjustment
		thisLevel = level if adjustment > 0 else nextLevel
		level = nextLevel

		# Trim
		if not inComment:
			m = re.match(r'^(\s+)\/\*.*', lines[i])
			if m is not None:
				outPrefix = m.group(1)
				lines[i] = re.sub(r'^' + outPrefix + '(.*)\s*$', r'\1', lines[i])
			else:
				lines[i] = re.sub(r'^\s*(.*)\s*$', r'\1', lines[i])
		else:
			lines[i] = re.sub(r'^' + outPrefix + '(.*)\s*$', r'\1', lines[i])

		# Is next line in comment?
		commentQuotes = re.findall(r'\/\*|\*\/', lines[i])
		for quote in commentQuotes:
			if inComment and quote == '*/':
				inComment = False
			elif quote == '/*':
				inComment = True

		# Add Indentation
		lines[i] = indentation * thisLevel + lines[i] if lines[i] != '' else ''

	code = '\n'.join(lines)

	return code
