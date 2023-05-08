#Filipe Chagas, 2023

import ply.lex as lex

#This is a dictionary of reserved language words. 
#It is necessary to create this dictionary so that lexer does not return these tokens as generic identifiers.
reserved = {
    'true': 'TRUE',
    'false': 'FALSE',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'in': 'IN',
    'amplify': 'AMPLIFY',
    'times': 'TIMES',
}

#This is a list with the names of the tokens.
tokens = [
   'NUMBER',
   'ID',
   # --- arithmetic ---
   'PLUS',
   'MINUS',
   'MUL',
   'DIVIDE',
   'HAT',
   # --- relational ---
   'EQUAL',
   'NEQ',
   'LT',
   'GT',
   # --- others ---
   'COMMA',
   'ASSIGN',
   'SEMICOLON',
   'LPAREN',
   'RPAREN',
   'LCURLY',
   'RCURLY',
   'LBRACKET',
   'RBRACKET'
] + list(reserved.values())

#Next, we define the regular expressions for the tokens
# --- arithmetic ---
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_MUL   = r'\*'
t_DIVIDE  = r'/'
t_HAT  = r'\^'

# --- relational ---
t_EQUAL  = r'='
t_NEQ = r'!='
t_LT = r'<'
t_GT = r'>'

# --- others ---
t_COMMA = r','
t_ASSIGN  = r':='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LCURLY  =  r'\{'
t_RCURLY  =  r'\}'
t_LBRACKET  =  r'\['
t_RBRACKET  =  r'\]'
t_SEMICOLON  =  r';'

#Next, we define the regex of numbers and identifiers (or reserved words)
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'ID') #Check for reserved words
    return t

#Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

#A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

#Defines a custom exception for lexical errors
class LexicalError(Exception):
    def __init__(self, token) -> None:
        super().__init__(f'Illegal character {token.value[0]}')

#Error handling rule
def t_error(t):
    raise LexicalError(t)

#Build the lexer
lexer = lex.lex()