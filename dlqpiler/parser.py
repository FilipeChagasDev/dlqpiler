#Filipe Chagas, 2023

from dlqpiler.lexer import *
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

# --- Parsing rules to statements ---

#Root parsing rule
def p_full_code(p):
    'fullcode : regdefseq amplifyterm'
    p[0] = ast.FullCode(p.lineno(0), p[1], p[2])

#Syntax of the amplify terminator
def p_amplify_terminator(p):
    'amplifyterm : AMPLIFY ID NUMBER TIMES'
    target = p[2]
    it = p[3]

    if it < 0:
        raise ParsingError(p.lineno(0), 'The number of amplify iterations must be greater or equal to 0')
    
    p[0] = ast.Amplify(p.lineno(0), target, it)

#Syntax of a sequence of register definitions separated by semicolons
def p_regdef_sequence_body(p):
    'regdefseq : regdef SEMICOLON regdefseq'
    p[0] = [p[1]] + p[3]

def p_regdef_sequence_tail(p):
    'regdefseq : regdef SEMICOLON'
    p[0] = [p[1]]

#A register definition statement, that can be by set or by expression
def p_register_definition(p):
    '''regdef : regdefs
              | regdefx'''
    p[0] = p[1]

#Statement for the definition of a register as a set
#Example: "myreg[8] in {1, 2, 3}" defines an 8-bit register as a superposition of 1, 2 and 3
def p_register_definition_set(p):
    'regdefs : ID LBRACKET NUMBER RBRACKET IN LCURLY expseq RCURLY'
    id = p[1]
    n = p[3]
    seq = p[7]
    
    if n <= 0:
        raise ParsingError(p.lineno(0), 'Register\'s size must be greater than 0')
    
    if not all([isinstance(v, int) for v in seq]):
        raise ParsingError(p.lineno(0), 'A set must be composed only of constant values')
    
    p[0] = ast.RegisterSetDefinition(p.lineno(0), id, n, set(seq))

#Statement for the definition of a register as an expression
#Example: "myreg[8] := b^2 - 4*a*c" defines an 8-bit register as b^2-4*a*c
def p_register_definition_expression(p):
    'regdefx : ID LBRACKET NUMBER RBRACKET ASSIGN expression'
    id = p[1]
    n = p[3]
    expr = p[6]

    if n <= 0:
        raise ParsingError(p.lineno(0), 'Register\'s size must be greater than 0')
        
    if isinstance(expr, (ast.Identifier, int)):
        raise ParsingError(p.lineno(0), 'dlqpiler currently does not accept direct assignments or constants in registers, only logical, arithmetic and relational expressions.')

    p[0] = ast.RegisterExpressionDefinition(p.lineno(0), id, n, expr)


# --- Parsing rules to expression sequences ---
def p_expression_sequence_fork(p):
    'expseq : expseq COMMA expression'
    p[0] = p[1] + [p[3]]

def p_expression_sequence_tail(p):
    'expseq : expression'
    p[0] = [p[1]]

# --- Parsing rules to logic expressions ---
def p_expression_or(p):
    'expression : expression OR expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = int(bool(p[1] % 2) or bool(p[3] % 2))
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.Or.merge(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the OR operator to types {(type(p[1]), type(p[3]))}')
    
def p_expression_and(p):
    'expression : expression AND expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = int(bool(p[1] % 2) and bool(p[3] % 2))
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.And.merge(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the AND operator to types {(type(p[1]), type(p[3]))}')

def p_expression_not(p):
    'expression : NOT expression'    
    if isinstance(p[2], int):
        p[0] = int(not bool(p[2] % 2))
    elif isinstance(p[2], (ast.Expression, int)):
        p[0] = ast.Not(p.lineno(0), p[2])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the NOT operator to type {type(p[2])}')
    
# --- Parsing rules to relational expressions ---

#Parsing rule to the equal operator ('=')
def p_expression_equal(p):
    'expression : expression EQUAL expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] == p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.Equal(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the equal operator to types {(type(p[1]), type(p[3]))}')

#Parsing rule to the not-equal operator ('!=')
def p_expression_not_equal(p):
    'expression : expression NEQ expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] != p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.NotEqual(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the not-equal operator to types {(type(p[1]), type(p[3]))}')

#Parsing rule to the less-than operator ('<')
def p_expression_less_than(p):
    'expression : expression LT expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] < p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.LessThan(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the less-than operator to types {(type(p[1]), type(p[3]))}')

#Parsing rule to the greater-than operator ('>')
def p_expression_greater_than(p):
    'expression : expression GT expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] > p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.GreaterThan(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the greater-than operator to types {(type(p[1]), type(p[3]))}')

# --- Parsing rules to arithmetic expressions ---

#Parsing rule to the addition operator ('+')
def p_expression_add(p):
    'expression : expression PLUS expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] + p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.Summation.merge_add(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the addition operator to types {(type(p[1]), type(p[3]))}')

#Parsing rule to the subtraction operator ('-')
def p_expression_sub(p):
    'expression : expression MINUS expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] - p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.Summation.merge_sub(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the subtraction operator to types {(type(p[1]), type(p[3]))}')

#Parsing rule to the multiplication operator ('*')
def p_expression_mul(p):
    'expression : expression MUL expression'
    if isinstance(p[1], int) and isinstance(p[3], int):
        p[0] = p[1] * p[3]
    elif isinstance(p[1], (ast.Expression, int)) and isinstance(p[3], (ast.Expression, int)):
        p[0] = ast.Product.merge(p.lineno(0), p[1], p[3])
    else:
        raise ParsingError(p.lineno(0), f'It is not possible to apply the product operator to types {(type(p[1]), type(p[3]))}')
    
#Parsing rule to the division operator ('^')
def p_expression_power(p):
    'expression : expression HAT expression'
    if isinstance(p[3], int):
        if isinstance(p[1], ast.Expression):
            p[0] = ast.Power(p.lineno(0), p[1], p[3])
        elif isinstance(p[1], int):
            p[0] = p[1]**p[3]
        else:
            raise ParsingError(p.lineno(0), f'It\'s not possible to apply the power operator to a base of type {type(p[1])}')
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
    if isinstance(p[2], ast.Expression):
        p[0] = ast.UnaryMinus(p.lineno(0), p[2])
    elif isinstance(p[2], int):
        p[0] = -p[2]
    else:
        raise ParsingError(p.lineno(0), f'It\'s not possible to apply the unary minus operator to {type(p[2])}')

#Parsing rule to expressions in parentheses
def p_expression_parentheses(p):
    'expression : LPAREN expression RPAREN'
    if isinstance(p[2], int): #If the inner expression is a value, return the value
        p[0] = p[2]
    else:
        p[0] = ast.Parentheses(p.lineno(0), p[2])

# --- Parsing rules to values and identifiers ---

def p_expression_false(p):
    'expression : FALSE'
    p[0] = 0

def p_expression_true(p):
    'expression : TRUE'
    p[0] =  1

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