#Filipe Chagas, 2023

from typing import *

class ASTNode():
    def __init__(self, line: int) -> None:
        assert isinstance(line, int)
        self.line = line

    def to_dict(self):
        return dict()

# --- Expression AST nodes ---

class Expression(ASTNode):
    def __init__(self, line: int) -> None:
        super().__init__(line)

class Parentheses(Expression):
    def __init__(self, line: int, inner_expr: Expression) -> None:
        super().__init__(line)
        assert isinstance(inner_expr, Expression)
        self.inner_expr = inner_expr

    def to_dict(self):
        return {'type': 'Parentheses', 'inner_expr': self.inner_expr.to_dict()}
    
# --- Arithmetic expression AST nodes ---

class ArithmeticExpression(Expression):
    def __init__(self, line: int) -> None:
        super().__init__(line)

class UnaryMinus(ArithmeticExpression):
    def __init__(self, line: int, inner_expr: ArithmeticExpression) -> None:
        super().__init__(line)
        assert isinstance(inner_expr, ArithmeticExpression)
        self.inner_expr = inner_expr

    def to_dict(self):
        return {'type': 'UnaryMinus', 'inner_expr': self.inner_expr.to_dict()}
    
class Power(ArithmeticExpression):
    def __init__(self, line: int, base_expr: ArithmeticExpression, exponent: int) -> None:
        super().__init__(line)
        assert isinstance(base_expr, ArithmeticExpression)
        assert isinstance(exponent, int)
        self.base_expr = base_expr
        self.exponent = exponent

    def to_dict(self):
        return {'type': 'Power', 'base_expr': self.base_expr.to_dict(), 'exponent': self.exponent}