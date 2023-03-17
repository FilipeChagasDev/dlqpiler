#Filipe Chagas, 2023

from dlqpiler import lexer
from dlqpiler import ast
import ply.yacc as yacc

#Defines a custom exception for parsing errors
class ParsingError(Exception):
    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        if isinstance(line, int): #Check if line is not None
            super().__init__(f'Parsing error at line {line}: {message}')
        else:
            super().__init__(f'Parsing error at EOF: {message}')

#Defines the precedence and associativity of unary and binary operators
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'LT', 'GT'),
    ('left', 'EQUAL', 'NEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIVIDE'),
    ('right', 'UMINUS'),
    ('right', 'HAT'),
)

# --- Parsing rules to arithmetic expressions ---

#Parsing rule to the multiplication operator ('*')
def p_expression_mul(p):
    'expression : expression MUL expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1]*p[2]
    elif isinstance(p[1], (ast.ArithmeticExpression, ast.Identifier, int)) and isinstance(p[3], (ast.ArithmeticExpression, ast.Identifier, int)):
        p[0] = ast.Product.merge(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), 'The product operator can only be used with numerical values or arithmetic expressions as operators')
    
#Parsing rule to the division operator ('^')
def p_expression_power(p):
    'expression : expression HAT expression'
    if isinstance(p[3], int):
        if isinstance(p[1], (ast.ArithmeticExpression, ast.Identifier)):
            p[0] = ast.Power(p.lineno(0), p[1], p[3])
        elif isinstance(p[1], int):
            p[0] = p[1]**p[3]
        else:
            raise ParsingError(p.lineno(0), 'The power operator can only be used with numerical values or arithmetic expressions as base')
    else:
        raise ParsingError(p.lineno(0), 'The power operator can only be used with constant exponent')
    
#Parsing rule to the division operator ('/')
def p_expression_division(p):
    'expression : expression DIVIDE expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1]//p[3]
    else:
        raise ParsingError(p.lineno(0), 'The division operator can only be applied to constant numeric values')

#Parsing rule to unary minus
def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    if isinstance(p[2], (ast.ArithmeticExpression, ast.Identifier)):
        p[0] = ast.UnaryMinus(p.lineno(0), p[2])
    elif isinstance(p[2], int):
        p[0] = -p[2]
    else:
        raise ParsingError(p.lineno(0), 'The unary minus operator can only be applied to numeric values and arithmetic expressions')

#Parsing rule to expressions in parentheses
def p_expression_parentheses(p):
    'expression : LPAREN expression RPAREN'
    if isinstance(p[2], (int, bool)): #If the inner expression is a value, return the value
        p[0] = p[2]
    else:
        p[0] = ast.Parentheses(p.lineno(0), p[2])

# --- Parsing rules to values and identifiers ---

def p_expression_false(p):
    'expression : FALSE'
    p[0] = False

def p_expression_true(p):
    'expression : TRUE'
    p[0] = True

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]

def p_expression_id(p):
    'expression : ID'
    p[0] = ast.Identifier(p.lineno(0), p[1])

#Defines a function to handle syntax errors
def p_error(p):
    if p:
        raise ParsingError(p.lineno(0), 'Invalid syntax')
    else:
        raise ParsingError(None, 'Invalid syntax')

#Build the parser
parser = yacc.yacc()