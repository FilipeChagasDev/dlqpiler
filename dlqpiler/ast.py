#Filipe Chagas, 2023

from typing import *
from enum import Enum

class Signal(Enum):
    POS = True #Positive signal
    NEG = False #Negative signal

class ASTNode():
    def __init__(self, line: int) -> None:
        """
        :param line: Line of code
        :type line: int
        """
        assert isinstance(line, int)
        self.line = line

    def to_dict(self) -> Dict[str, object]:
        """
        Recursively convert the AST to a tree of dictionaries

        :return: Tree of dictionaries
        :rtype: Dict[str, object]
        """
        return dict()

# --- Expression AST nodes ---

class Expression(ASTNode):
    def __init__(self, line: int) -> None:
        super().__init__(line)

class Identifier(Expression):
    def __init__(self, line: int, label: str) -> None:
        """
        :param line: Line of code
        :type line: int
        :param label: Text of the identifier
        :type label: str
        """
        super().__init__(line)
        assert isinstance(label, str)
        self.label = label

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Identifier', 'label': self.label}

class Parentheses(Expression):
    def __init__(self, line: int, inner_expr: Expression) -> None:
        """
        :param line: Line of code
        :type line: int
        :param inner_expr: Expression in parentheses
        :type inner_expr: Expression
        """
        super().__init__(line)
        assert isinstance(inner_expr, Expression)
        self.inner_expr = inner_expr

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Parentheses', 'inner_expr': self.inner_expr.to_dict()}
    
# --- Arithmetic expression AST nodes ---

class ArithmeticExpression(Expression):
    def __init__(self, line: int) -> None:
        """
        :param line: Line of code
        :type line: int
        """
        super().__init__(line)

class UnaryMinus(ArithmeticExpression):
    def __init__(self, line: int, inner_expr: Union[ArithmeticExpression, Identifier]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param inner_expr: Expression to which the unary minus is being applied
        :type inner_expr: Union[ArithmeticExpression, Identifier]
        """
        super().__init__(line)
        assert isinstance(inner_expr, (ArithmeticExpression, Identifier))
        self.inner_expr = inner_expr

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'UnaryMinus', 'inner_expr': self.inner_expr.to_dict()}
    
class Power(ArithmeticExpression):
    def __init__(self, line: int, base_expr: Union[ArithmeticExpression, Identifier], exponent: int) -> None:
        """
        :param line: Line of code
        :type line: int
        :param base_expr: Expression that is used as base
        :type base_expr: Union[ArithmeticExpression, Identifier]
        :param exponent: Integer that is used as exponent
        :type exponent: int
        """
        super().__init__(line)
        assert isinstance(base_expr, (ArithmeticExpression, Identifier))
        assert isinstance(exponent, int)
        self.base_expr = base_expr
        self.exponent = exponent

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Power', 'base_expr': self.base_expr.to_dict(), 'exponent': self.exponent}
    
class Product(ArithmeticExpression):
    def __init__(self, line: int, operands: List[Union[ArithmeticExpression, Identifier, int]], signals: List[Signal]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param operands: Operands of the productory
        :type operands: List[Union[ArithmeticExpression, Identifier, int]]
        :param signals: List with the signals of the operands
        :type signals: List[Signal]
        """
        super().__init__(line)
        assert isinstance(operands, list)
        assert isinstance(signals, list)
        assert all([isinstance(op, (ArithmeticExpression, Identifier, int)) for op in operands])
        assert all([isinstance(sig, Signal) for sig in signals])
        self.operands = operands
        self.signals = signals

    @staticmethod
    def merge(line: int, left: Union[ArithmeticExpression, Identifier, int], right: Union[ArithmeticExpression, Identifier, int]) -> object:
        """Return a Product object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[ArithmeticExpression, Identifier, int]
        :param right: Right operand
        :type right: Union[ArithmeticExpression, Identifier, int]
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, (ArithmeticExpression, Identifier, int))
        assert isinstance(right, (ArithmeticExpression, Identifier, int))
        left_operands_list = left.operands if isinstance(left, Product) else [left]
        right_operands_list = right.operands if isinstance(right, Product) else [right]
        left_signals_list = left.signals if isinstance(left, Product) else [Signal.POS]
        right_signals_list = right.signals if isinstance(right, Product) else [Signal.POS]
        return Product(line, left_operands_list + right_operands_list, left_signals_list + right_signals_list)

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Product',
            'operands': [(op.to_dict() if isinstance(op, Expression) else op) for op in self.operands],
            'signals': [('+' if sig == Signal.POS else '-') for sig in self.signals]
        }