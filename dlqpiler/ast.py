#Filipe Chagas, 2023

from typing import *
from enum import Enum
from typing import Dict, Union

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
    def __init__(self, line: int, inner_expr: Expression) -> None:
        """
        :param line: Line of code
        :type line: int
        :param inner_expr: Expression to which the unary minus is being applied
        :type inner_expr: Expression
        """
        super().__init__(line)
        assert isinstance(inner_expr, Expression)
        self.inner_expr = inner_expr

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'UnaryMinus', 'inner_expr': self.inner_expr.to_dict()}
    
class Power(ArithmeticExpression):
    def __init__(self, line: int, base_expr: Expression, exponent: int) -> None:
        """
        :param line: Line of code
        :type line: int
        :param base_expr: Expression that is used as base
        :type base_expr: Expression
        :param exponent: Integer that is used as exponent
        :type exponent: int
        """
        super().__init__(line)
        assert isinstance(base_expr, Expression)
        assert isinstance(exponent, int)
        self.base_expr = base_expr
        self.exponent = exponent

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Power', 'base_expr': self.base_expr.to_dict(), 'exponent': self.exponent}
    
class Product(ArithmeticExpression):
    def __init__(self, line: int, operands: List[Union[Expression, int]], signals: List[Signal]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param operands: Operands of the productory
        :type operands: List[Union[Expression, int]]
        :param signals: List with the signals of the operands
        :type signals: List[Signal]
        """
        super().__init__(line)
        assert isinstance(operands, list)
        assert isinstance(signals, list)
        assert all([isinstance(op, (Expression, int)) for op in operands])
        assert all([isinstance(sig, Signal) for sig in signals])
        self.operands = operands
        self.signals = signals

    @staticmethod
    def merge(line: int, left: Union[Expression, int], right: Union[Expression, int]) -> object:
        """Return a Product object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        left_operands_list = left.operands if isinstance(left, Product) else [left]
        right_operands_list = [right]
        left_signals_list = left.signals if isinstance(left, Product) else [Signal.POS]
        right_signals_list = [Signal.POS]
        return Product(line, left_operands_list + right_operands_list, left_signals_list + right_signals_list)

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Product',
            'operands': [(op.to_dict() if isinstance(op, Expression) else op) for op in self.operands],
            'signals': [('+' if sig == Signal.POS else '-') for sig in self.signals]
        }
    
class Summation(ArithmeticExpression):
    def __init__(self, line: int, operands: List[Union[Expression, int]], signals: List[Signal]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param operands: Operands of the summation
        :type operands: List[Union[Expression, int]]
        :param signals: List with the signals of the operands
        :type signals: List[Signal]
        """
        super().__init__(line)
        assert isinstance(operands, list)
        assert isinstance(signals, list)
        assert all([isinstance(op, (Expression, int)) for op in operands])
        assert all([isinstance(sig, Signal) for sig in signals])
        self.operands = operands
        self.signals = signals

    @staticmethod
    def merge_add(line: int, left: Union[Expression, int], right: Union[Expression, int]) -> object:
        """Return a Summation object to a pair of addition operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        :return: Summation object
        :rtype: Summation
        """
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        left_operands_list = left.operands if isinstance(left, Summation) else [left]
        right_operands_list = [right]
        left_signals_list = left.signals if isinstance(left, Summation) else [Signal.POS]
        right_signals_list = [Signal.POS]
        return Summation(line, left_operands_list + right_operands_list, left_signals_list + right_signals_list)

    @staticmethod
    def merge_sub(line: int, left: Union[Expression, int], right: Union[Expression, int]) -> object:
        """Return a Summation object to a pair of subtraction operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        :return: Summation object
        :rtype: Summation
        """
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        left_operands_list = left.operands if isinstance(left, Summation) else [left]
        right_operands_list = [right]
        left_signals_list = left.signals if isinstance(left, Summation) else [Signal.POS]
        right_signals_list = [Signal.NEG]
        return Summation(line, left_operands_list + right_operands_list, left_signals_list + right_signals_list)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Summation',
            'operands': [(op.to_dict() if isinstance(op, Expression) else op) for op in self.operands],
            'signals': [('+' if sig == Signal.POS else '-') for sig in self.signals]
        }
    
# --- Relational expression AST nodes ---

class RelationalExpression(Expression):
    def __init__(self, line: int, left: Union[Expression, int], right: Union[Expression, int]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        """
        super().__init__(line)
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        self.left = left
        self.right = right

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': self.__class__.__name__,
            'left': self.left if isinstance(self.left, int) else self.left.to_dict(),
            'right': self.right if isinstance(self.right, int) else self.right.to_dict()
        }

class Equal(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

class NotEqual(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

class LessThan(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

class GreaterThan(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

# --- logic expression AST nodes ---

class LogicExpression(Expression):
    def __init__(self, line: int) -> None:
        """
        :param line: Line of code
        :type line: int
        """
        super().__init__(line)

class Not(LogicExpression):
    def __init__(self, line: int, operand: Expression) -> None:
        super().__init__(line)
        assert isinstance(operand, Expression)
        self.operand = operand

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Not',
            'operand': self.operand if isinstance(self.operand, int) else self.operand.to_dict()
        }
    
class And(LogicExpression):
    def __init__(self, line: int, operands: List[Union[Expression, int]]) -> None:
        super().__init__(line)
        assert all([isinstance(operand, (Expression, int)) for operand in operands])
        self.operands = operands

    @staticmethod
    def merge(line: int, left: Union[Expression, int], right: Union[Expression, int]) -> object:
        """Return a And object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        left_operands_list = left.operands if isinstance(left, And) else [left]
        right_operands_list = [right]
        return And(line, left_operands_list + right_operands_list)

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'And',
            'operands': [(op if isinstance(op, int) else op.to_dict()) for op in self.operands]
        }
    
class Or(LogicExpression):
    def __init__(self, line: int, operands: List[Union[Expression, int]]) -> None:
        super().__init__(line)
        assert all([isinstance(operand, (Expression, int)) for operand in operands])
        self.operands = operands

    @staticmethod
    def merge(line: int, left: Union[Expression, int], right: Union[Expression, int]) -> object:
        """Return a Or object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Union[Expression, int]
        :param right: Right operand
        :type right: Union[Expression, int]
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, (Expression, int))
        assert isinstance(right, (Expression, int))
        left_operands_list = left.operands if isinstance(left, Or) else [left]
        right_operands_list = [right]
        return Or(line, left_operands_list + right_operands_list)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Or',
            'operands': [(op if isinstance(op, int) else op.to_dict()) for op in self.operands]
        }
    
# --- Register definition AST nodes ---

class RegisterExpressionDefinition(ASTNode):
    def __init__(self, line: int, name: str, n: int, expr: Expression) -> None:
        """
        :param line: Line of code
        :type line: int
        :param name: Register's name
        :type name: str
        :param n: Register's size
        :type n: int
        :param expr: Target expression
        :type expr: Expression
        """
        super().__init__(line)
        assert isinstance(name, str)
        assert isinstance(n, int)
        assert isinstance(expr, Expression)
        self.name = name
        self.n = n
        self.expr = expr

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'RegisterExpressionDefinition',
            'name': self.name,
            'size': self.n,
            'expr': self.expr.to_dict()
        }
    
class RegisterSetDefinition(ASTNode):
    def __init__(self, line: int, name: str, n: int, values: Set[int]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param name: Register's name
        :type name: str
        :param n: Register's size
        :type n: int
        :param expr: Target expression
        :type expr: Expression
        """
        super().__init__(line)
        assert isinstance(name, str)
        assert isinstance(n, int)
        assert all([isinstance(v, int) for v in values])
        self.name = name
        self.n = n
        self.values = values

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'RegisterSetDefinition',
            'name': self.name,
            'size': self.n,
            'values': self.values
        }
    
# --- Terminators ---

class Terminator(ASTNode):
    def __init__(self, line: int) -> None:
        super().__init__(line)

class Amplify(Terminator):
    def __init__(self, line: int, target: str, iterations: int) -> None:
        super().__init__(line)
        assert isinstance(target, str)
        assert isinstance(iterations, int)
        self.target = target
        self.it = iterations

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Amplify',
            'target': self.target,
            'iterations': self.it
        }
    
# --- Full code AST node ---

class FullCode(ASTNode):
    def __init__(self, line: int, regdefseq: List[Union[RegisterExpressionDefinition, RegisterSetDefinition]], terminator: Terminator) -> None:
        super().__init__(line)
        assert isinstance(regdefseq, list)
        assert all([isinstance(x, (RegisterExpressionDefinition, RegisterSetDefinition)) for x in regdefseq])
        assert isinstance(terminator, Terminator)
        self.regdefseq = regdefseq
        self.terminator = terminator

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'FullCode',
            'sequence': [x.to_dict() for x in self.regdefseq],
            'terminator': self.terminator.to_dict()
        }
    