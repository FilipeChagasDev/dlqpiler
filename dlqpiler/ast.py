#Filipe Chagas, 2023

from typing import *
from enum import Enum
from typing import Set
from dlqpiler import utils, qunits
import qiskit
import math

n_bits_const = lambda c: int(math.ceil(math.log2(c))) if c > 0 else 0

class SynthError(Exception):
    def __init__(self, line: int, description: str) -> None:
        self.line = line
        self.description = description
        super().__init__(f'Synthesis error at line {line}: {description}')

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
        self.result = None

    def get_leafs(self) -> Set[str]:
        """Return a set with all identifiers used in the expression

        :return: self-descriptive
        :rtype: Set[str]
        """
        return set()
    
    def needs_result_allocation(self) -> bool:
        """
        :return: True if the ASTNode needs allocation of result qubits
        :rtype: bool
        """
        return True

    def n_result_qubits(self, quantum_evaluator) -> int:
        """
        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        :raises NotImplementedError: self-descriptive
        :return: Number of necessary result qubits
        :rtype: int
        """
        raise NotImplementedError()
    
    def alloc_result_qubits(self, quantum_evaluator):
        """Allocate the result qubits from the quantum evaluator

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        """
        assert utils.is_none(self.result)
        self.result = [quantum_evaluator.alloc_ancilla() for i in range(self.n_result_qubits(quantum_evaluator))]

    def release_result_qubits(self, quantum_evaluator):
        """Release the clean result qubits

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        """
        assert not utils.is_none(self.result)
        for qb in self.result:
            quantum_evaluator.free_ancilla(qb)
        self.result = None

    def pre_build(self, quantum_evaluator):
        """Do the necessary actions before the build operation

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        """
        pass
    
    def build(self, quantum_evaluator):
        """Build the quantum circuit recursively

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        :raises NotImplementedError: self-descriptive
        """
        raise NotImplementedError()

    def reverse(self, quantum_evaluator):
        """Build the inverse quantum circuit recursively

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        :raises NotImplementedError: self-descriptive
        """
        raise NotImplementedError()

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

    def get_leafs(self) -> Set[str]:
        return {self.label}

    def n_result_qubits(self, quantum_evaluator) -> int:
        n = quantum_evaluator.get_register_size(self.label)
        if utils.is_none(n):
            raise SynthError(self.line, f'Identifier "{self.label}" not defined')
        return n
    
    def needs_result_allocation(self) -> bool:
        return False

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Identifier', 'label': self.label}

    def pre_build(self, quantum_evaluator):
        qreg = quantum_evaluator.get_qiskit_register(self.label)
        if utils.is_none(qreg):
            raise SynthError(self.line, f'Identifier "{self.label}" not defined')
        self.result = [qubit for qubit in qreg]

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

    def get_leafs(self) -> Set[str]:
        return self.inner_expr.get_leafs()

    def n_result_qubits(self, quantum_evaluator) -> int:
        return self.inner_expr.n_result_qubits(quantum_evaluator)

    def needs_result_allocation(self) -> bool:
        return False
    
    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Parentheses', 'inner_expr': self.inner_expr.to_dict()}

    @staticmethod
    def bypass(expr: Expression) -> Expression:
        """If expr is a Parentheses node or a chain of multiple Parentheses nodes, it returns the first inner not-Parentheses expression.

        :param expr: self-descriptive
        :type expr: Expression
        :return: Inner non-Parentheses expression
        :rtype: Expression
        """
        x = expr
        while isinstance(x, Parentheses):
            x = x.inner_expr
        return x
    
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
        self.needs_result_allocation = False
        assert isinstance(inner_expr, Expression)
        self.inner_expr = inner_expr

    def get_leafs(self) -> Set[str]:
        return self.inner_expr.get_leafs()

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

    def get_leafs(self) -> Set[str]:
        return self.base_expr.get_leafs()

    def to_dict(self) -> Dict[str, object]:
        return {'type': 'Power', 'base_expr': self.base_expr.to_dict(), 'exponent': self.exponent}
    
    def n_result_qubits(self, quantum_evaluator) -> int:
        nb = self.base_expr.n_result_qubits(quantum_evaluator)
        return nb*self.exponent
    
    def pre_build(self, quantum_evaluator):
        self.base_expr.pre_build(quantum_evaluator)
        self.base_expr = Parentheses.bypass(self.base_expr)
        
    def build(self, quantum_evaluator) -> List[qiskit.circuit.Qubit]:
        if self.base_expr.needs_result_allocation():
            self.base_expr.alloc_result_qubits(quantum_evaluator)
        
        if not isinstance(self.base_expr, Identifier):
            self.base_expr.build(quantum_evaluator)
        
        qunits.multiproduct(quantum_evaluator.quantum_circuit, [self.base_expr.result], [self.exponent], self.result)        

    def reverse(self, quantum_evaluator) -> List[qiskit.circuit.Qubit]:
        qunits.multiproduct_dg(quantum_evaluator.quantum_circuit, [self.base_expr.result], [self.exponent], self.result)

        if not isinstance(self.base_expr, Identifier):
            self.base_expr.reverse(quantum_evaluator)

        if self.base_expr.needs_result_allocation():
            self.base_expr.release_result_qubits(quantum_evaluator)

class Product(ArithmeticExpression):
    def __init__(self, line: int, operands: List[Union[Expression, int]]) -> None:
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
        assert all([isinstance(op, (Expression, int)) for op in operands])
        self.operands = operands
        self.exponents = [1]*len(self.operands)
        self.const_factor = 1
        self.filtered_operands = []
        self.filtered_exponents = []

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
        return Product(line, left_operands_list + right_operands_list)

    def get_leafs(self) -> Set[str]:
        leafs = set()
        for op in self.operands:
            if isinstance(op, Expression):
                leafs = leafs.union(op.get_leafs())
        return leafs
    
    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Product',
            'operands': [(op.to_dict() if isinstance(op, Expression) else op) for op in self.operands]
        }
    
    def n_result_qubits(self, quantum_evaluator) -> int:
        return sum([self.filtered_operands[i].n_result_qubits(quantum_evaluator)*self.filtered_exponents[i] for i in range(len(self.filtered_operands))]) + n_bits_const(self.const_factor)
    
    def pre_build(self, quantum_evaluator):
        #--- merge power operations ---
        for i in range(len(self.operands)):
            if isinstance(self.operands[i], int):
                self.const_factor *= self.operands[i]
            else:
                self.operands[i].pre_build(quantum_evaluator)
                while isinstance(self.operands[i], (Power, Parentheses)):
                    self.operands[i] = Parentheses.bypass(self.operands[i])
                    if isinstance(self.operands[i], Power):
                        self.operands[i] = self.operands[i].base_expr
                        self.exponents[i] *= self.operands[i].exponent
                self.filtered_operands.append(self.operands[i])
                self.filtered_exponents.append(self.exponents[i])

    def build(self, quantum_evaluator):
        for op in self.filtered_operands:
            if op.needs_result_allocation():
                op.alloc_result_qubits(quantum_evaluator)
            
            if not isinstance(op, Identifier):
                op.build(quantum_evaluator)

        qunits.multiproduct(quantum_evaluator.quantum_circuit, [op.result for op in self.filtered_operands], self.filtered_exponents, self.result)

    def reverse(self, quantum_evaluator):
        qunits.multiproduct_dg(quantum_evaluator.quantum_circuit, [op.result for op in self.filtered_operands], self.filtered_exponents, self.result)

        for op in self.operands:
            if not isinstance(op, Identifier):
                op.reverse()

            if op.needs_result_allocation():
                op.release_result_qubits(quantum_evaluator)

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
        self.const_term = 0
        self.filtered_operands = []
        self.filtered_signals = []

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
    
    def get_leafs(self) -> Set[str]:
        leafs = set()
        for op in self.operands:
            if isinstance(op, Expression):
                leafs = leafs.union(op.get_leafs())
        return leafs
    
    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Summation',
            'operands': [(op.to_dict() if isinstance(op, Expression) else op) for op in self.operands],
            'signals': [('+' if sig == Signal.POS else '-') for sig in self.signals]
        }
    
    def pre_build(self, quantum_evaluator):
        for i in range(len(self.operands)):
            if isinstance(self.operands[i], int):
                self.const_term += self.operands[i] if self.signals[i] == Signal.POS else -self.operands[i]
            else:
                self.operands[i].pre_build(quantum_evaluator)
                while isinstance(self.operands[i], (Parentheses, UnaryMinus)):
                    self.operands[i] = Parentheses.bypass(self.operands[i])
                    if isinstance(self.operands[i], UnaryMinus):
                        self.operands[i] = self.operands[i].inner_expr
                        self.signals[i] = Signal.POS if self.signals[i] == Signal.NEG else Signal.NEG
                self.filtered_operands.append(self.operands[i])
                self.filtered_signals.append(self.signals[i])

    def n_result_qubits(self, quantum_evaluator) -> int:
        return max([op.n_result_qubits(quantum_evaluator)+1 for op in self.filtered_operands] + [n_bits_const(self.const_term)])

    def build(self, quantum_evaluator):
        for i in range(len(self.filtered_operands)):
            #self.filtered_operands[i].pre_build(quantum_evaluator)
            if self.filtered_operands[i].needs_result_allocation():
                self.filtered_operands[i].alloc_result_qubits(quantum_evaluator)

            if not isinstance(self.filtered_operands[i], Identifier):
                self.filtered_operands[i].build(quantum_evaluator)

            if self.filtered_signals[i] == Signal.POS:
                qunits.register_by_register_addition(quantum_evaluator.quantum_circuit, self.filtered_operands[i].result, self.result)
            else:
                qunits.register_by_register_subtraction(quantum_evaluator.quantum_circuit, self.filtered_operands[i].result, self.result)
        
    def reverse(self, quantum_evaluator):
        for i in range(len(self.filtered_operands)):
            if self.filtered_signals[i] == Signal.POS:
                qunits.register_by_register_subtraction(quantum_evaluator.quantum_circuit, self.filtered_operands[i].result, self.result)
            else:
                qunits.register_by_register_addition(quantum_evaluator.quantum_circuit, self.filtered_operands[i].result, self.result)

            if not isinstance(self.filtered_operands[i], Identifier):
                self.filtered_operands[i].reverse(quantum_evaluator)

            if self.filtered_operands[i].needs_result_allocation():
                self.filtered_operands[i].release_result_qubits(quantum_evaluator)

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
        self.aux = None
        self.mode = '' #can be '', 'rr', 'rc' or 'cr'

    def get_leafs(self) -> Set[str]:
        if isinstance(self.left, Expression) and isinstance(self.right, Expression):
            return self.left.get_leafs().union(self.right.get_leafs())
        elif isinstance(self.left, Expression) and isinstance(self.right, int):
            return self.left.get_leafs()
        else:
            return self.right.get_leafs()

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': self.__class__.__name__,
            'left': self.left if isinstance(self.left, int) else self.left.to_dict(),
            'right': self.right if isinstance(self.right, int) else self.right.to_dict()
        }
    
    def n_result_qubits(self, quantum_evaluator) -> int:
        return 1
    
    def pre_build(self, quantum_evaluator):
        self.left = Parentheses.bypass(self.left)
        self.right = Parentheses.bypass(self.right)
        if isinstance(self.left, Expression) and isinstance(self.right, Expression):
            self.mode = 'rr'
        elif isinstance(self.left, Expression) and isinstance(self.right, int):
            self.mode = 'rc'
        else:
            self.mode = 'cr'

class Equal(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

    def pre_build(self, quantum_evaluator):
        super().pre_build(quantum_evaluator)
        if self.mode == 'rr':
            self.left.pre_build(quantum_evaluator)
            self.right.pre_build(quantum_evaluator)
            n = max([self.left.n_result_qubits(quantum_evaluator), self.right.n_result_qubits(quantum_evaluator)]) - min([self.left.n_result_qubits(quantum_evaluator), self.right.n_result_qubits(quantum_evaluator)])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'rc':
            self.left.pre_build(quantum_evaluator)
            n = max([math.ceil(math.log2(self.right)) - self.left.n_result_qubits(quantum_evaluator), 0])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'cr':
            self.right.pre_build(quantum_evaluator)
            n = max([math.ceil(math.log2(self.left)) - self.right.n_result_qubits(quantum_evaluator), 0])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        else:
            raise Exception('Undefined mode')
        
    def build(self, quantum_evaluator):
        if self.mode == 'rr':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_equal_register(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux, self.result[0])
        elif self.mode == 'rc':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            qunits.register_equal_constant(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
        elif self.mode == 'cr':
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_equal_constant(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
        else:
            raise Exception('Undefined mode')
        
    def reverse(self, quantum_evaluator):
        if self.mode == 'rr':
            qunits.register_equal_register_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits()
            if self.right.needs_result_allocation(): self.right.release_result_qubits()
        elif self.mode == 'rc':
            qunits.register_equal_constant_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
        elif self.mode == 'cr':
            qunits.register_equal_constant_dg(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        else:
            raise Exception('Undefined mode')
        
        for qbit in self.aux:
            quantum_evaluator.free_ancilla(qbit)

class NotEqual(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

    def pre_build(self, quantum_evaluator):
        super().pre_build(quantum_evaluator)
        if self.mode == 'rr':
            self.left.pre_build(quantum_evaluator)
            self.right.pre_build(quantum_evaluator)
            nl = self.left.n_result_qubits(quantum_evaluator)
            nr = self.right.n_result_qubits(quantum_evaluator)
            n = max([nl, nr]) - min([nl, nr])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'rc':
            self.left.pre_build(quantum_evaluator)
            n = max([math.ceil(math.log2(self.right)) - self.left.n_result_qubits(quantum_evaluator), 0])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'cr':
            self.right.pre_build(quantum_evaluator)
            n = max([math.ceil(math.log2(self.left)) - self.right.n_result_qubits(quantum_evaluator), 0])
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        else:
            raise Exception('Undefined mode')
        
    def build(self, quantum_evaluator):
        if self.mode == 'rr':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_not_equal_register(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux, self.result[0])
        elif self.mode == 'rc':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            qunits.register_not_equal_constant(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
        elif self.mode == 'cr':
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_not_equal_constant(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
        else:
            raise Exception('Undefined mode')
        
    def reverse(self, quantum_evaluator):
        if self.mode == 'rr':
            qunits.register_not_equal_register_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits()
            if self.right.needs_result_allocation(): self.right.release_result_qubits()
        elif self.mode == 'rc':
            qunits.register_not_equal_constant_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
        elif self.mode == 'cr':
            qunits.register_not_equal_constant_dg(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        else:
            raise Exception('Undefined mode')
        
        for qbit in self.aux:
            quantum_evaluator.free_ancilla(qbit)

class LessThan(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

    def pre_build(self, quantum_evaluator):
        super().pre_build(quantum_evaluator)
        if self.mode == 'rr':
            self.left.pre_build(quantum_evaluator)
            self.right.pre_build(quantum_evaluator)
            self.aux = [quantum_evaluator.alloc_ancilla()]
        elif self.mode == 'rc':
            self.left.pre_build(quantum_evaluator)
            nl = self.left.n_result_qubits(quantum_evaluator) 
            m = nl - max([nl, math.ceil(math.log2(self.right))])
            n = max([m, 0]) + 1
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'cr':
            self.right.pre_build(quantum_evaluator)
            nr = self.right.n_result_qubits(quantum_evaluator) 
            m = nr - max([nr, math.ceil(math.log2(self.left))])
            n = max([m, 0]) + 1
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        else:
            raise Exception('Undefined mode')
        
    def build(self, quantum_evaluator):
        if self.mode == 'rr':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_less_than_register(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux[0], self.result[0])
        elif self.mode == 'rc':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            qunits.register_less_than_constant(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
        elif self.mode == 'cr':
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_greater_than_constant(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
        else:
            raise Exception('Undefined mode')
        
    def reverse(self, quantum_evaluator):
        if self.mode == 'rr':
            qunits.register_less_than_register_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux[0], self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        elif self.mode == 'rc':
            qunits.register_less_than_constant_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
        elif self.mode == 'cr':
            qunits.register_greater_than_constant_dg(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        else:
            raise Exception('Undefined mode')
        
        for qbit in self.aux:
            quantum_evaluator.free_ancilla(qbit)

class GreaterThan(RelationalExpression):
    def __init__(self, line: int, left: Expression | int, right: Expression | int) -> None:
        super().__init__(line, left, right)

    def pre_build(self, quantum_evaluator):
        super().pre_build(quantum_evaluator)
        if self.mode == 'rr':
            self.left.pre_build(quantum_evaluator)
            self.right.pre_build(quantum_evaluator)
            self.aux = [quantum_evaluator.alloc_ancilla()]
        elif self.mode == 'rc':
            self.left.pre_build(quantum_evaluator)
            nl = self.left.n_result_qubits(quantum_evaluator) 
            m = nl - max([nl, math.ceil(math.log2(self.right))])
            n = max([m, 0]) + 1
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        elif self.mode == 'cr':
            self.right.pre_build(quantum_evaluator)
            nr = self.right.n_result_qubits(quantum_evaluator) 
            m = nr - max([nr, math.ceil(math.log2(self.left))])
            n = max([m, 0]) + 1
            self.aux = [quantum_evaluator.alloc_ancilla() for i in range(n)]
        else:
            raise Exception('Undefined mode')
        
    def build(self, quantum_evaluator):
        if self.mode == 'rr':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_greater_than_register(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux[0], self.result[0])
        elif self.mode == 'rc':
            if self.left.needs_result_allocation(): self.left.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.left, Identifier): self.left.build(quantum_evaluator)
            qunits.register_greater_than_constant(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
        elif self.mode == 'cr':
            if self.right.needs_result_allocation(): self.right.alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.build(quantum_evaluator)
            qunits.register_less_than_constant(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
        else:
            raise Exception('Undefined mode')
        
    def reverse(self, quantum_evaluator):
        if self.mode == 'rr':
            qunits.register_greater_than_register_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right.result, self.aux[0], self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        elif self.mode == 'rc':
            qunits.register_greater_than_constant_dg(quantum_evaluator.quantum_circuit, self.left.result, self.right, self.aux, self.result[0])
            if not isinstance(self.left, Identifier): self.left.reverse(quantum_evaluator)
            if self.left.needs_result_allocation(): self.left.release_result_qubits(quantum_evaluator)
        elif self.mode == 'cr':
            qunits.register_less_than_constant_dg(quantum_evaluator.quantum_circuit, self.right.result, self.left, self.aux, self.result[0])
            if not isinstance(self.right, Identifier): self.right.reverse(quantum_evaluator)
            if self.right.needs_result_allocation(): self.right.release_result_qubits(quantum_evaluator)
        else:
            raise Exception('Undefined mode')
        
        for qbit in self.aux:
            quantum_evaluator.free_ancilla(qbit)
        
# --- logic expression AST nodes ---

class LogicExpression(Expression):
    def __init__(self, line: int) -> None:
        """
        :param line: Line of code
        :type line: int
        """
        super().__init__(line)

    def n_result_qubits(self, quantum_evaluator) -> int:
        return 1

class Not(LogicExpression):
    def __init__(self, line: int, operand: Expression) -> None:
        """
        :param line: line of code
        :type line: int
        :param operand: self-descriptive
        :type operand: Expression
        """
        super().__init__(line)
        assert isinstance(operand, Expression)
        self.operand = operand

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Not',
            'operand': self.operand if isinstance(self.operand, int) else self.operand.to_dict()
        }

    def pre_build(self, quantum_evaluator):
        Parentheses.bypass(self.operand)
        self.operand.pre_build(quantum_evaluator)
    
    def build(self, quantum_evaluator):
        if self.operand.needs_result_allocation():
            self.operand.alloc_result_qubits(quantum_evaluator)
        if not isinstance(self.operand, Identifier):
            self.operand.build(quantum_evaluator)
        quantum_evaluator.quantum_circuit.cx(self.operand.result[-1], self.result[-1])
        quantum_evaluator.quantum_circuit.x(self.result[-1])

    def reverse(self, quantum_evaluator):
        quantum_evaluator.quantum_circuit.x(self.result[-1])
        quantum_evaluator.quantum_circuit.cx(self.operand.result[-1], self.result[-1])
        if not isinstance(self.operand, Identifier):
            self.operand.reverse(quantum_evaluator)
        if self.operand.needs_result_allocation():
            self.operand.release_result_qubits(quantum_evaluator)
    
class And(LogicExpression):
    def __init__(self, line: int, operands: List[Expression]) -> None:
        """
        :param line: line of code
        :type line: int
        :param operands: self-descriptive
        :type operands: List[Expression]
        """
        super().__init__(line)
        assert all([isinstance(operand, Expression) for operand in operands])
        self.operands = operands

    @staticmethod
    def merge(line: int, left: Expression, right: Expression) -> object:
        """Return a And object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Expression
        :param right: Right operand
        :type right: Expression
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, Expression)
        assert isinstance(right, Expression)
        left_operands_list = left.operands if isinstance(left, And) else [left]
        right_operands_list = [right]
        return And(line, left_operands_list + right_operands_list)

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'And',
            'operands': [(op if isinstance(op, int) else op.to_dict()) for op in self.operands]
        }
    
    def pre_build(self, quantum_evaluator):
        for i in range(len(self.operands)):
            self.operands[i] = Parentheses.bypass(self.operands[i])
            self.operands[i].pre_build(quantum_evaluator)

    def build(self, quantum_evaluator):
        for i in range(len(self.operands)):
            if self.operands[i].needs_result_allocation(): 
                self.operands[i].alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.operands[i], Identifier):
                self.operands[i].build(quantum_evaluator)
        quantum_evaluator.quantum_circuit.mcx([op.result[-1] for op in self.operands], self.result[-1])

    def reverse(self, quantum_evaluator):
        quantum_evaluator.quantum_circuit.mcx([op.result[-1] for op in self.operands], self.result[-1])
        for i in range(len(self.operands)):
            if not isinstance(self.operands[i], Identifier):
                self.operands[i].reverse(quantum_evaluator)
            if self.operands[i].needs_result_allocation(): 
                self.operands[i].release_result_qubits(quantum_evaluator)
    
class Or(LogicExpression):
    def __init__(self, line: int, operands: List[Expression]) -> None:
        """
        :param line: Line of code
        :type line: int
        :param operands: self-descriptive
        :type operands: List[Expression]
        """
        super().__init__(line)
        assert all([isinstance(operand, Expression) for operand in operands])
        self.operands = operands

    @staticmethod
    def merge(line: int, left: Expression, right: Expression) -> object:
        """Return a Or object to a pair of operands

        :param line: Line of code
        :type line: int
        :param left: Left operand
        :type left: Expression
        :param right: Right operand
        :type right: Expression
        :return: Product object
        :rtype: Product
        """
        assert isinstance(left, Expression)
        assert isinstance(right, Expression)
        left_operands_list = left.operands if isinstance(left, Or) else [left]
        right_operands_list = [right]
        return Or(line, left_operands_list + right_operands_list)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'Or',
            'operands': [(op if isinstance(op, int) else op.to_dict()) for op in self.operands]
        }
    
    def pre_build(self, quantum_evaluator):
        for i in range(len(self.operands)):
            self.operands[i] = Parentheses.bypass(self.operands[i])
            self.operands[i].pre_build(quantum_evaluator)

    def build(self, quantum_evaluator):
        for i in range(len(self.operands)):
            if self.operands[i].needs_result_allocation(): 
                self.operands[i].alloc_result_qubits(quantum_evaluator)
            if not isinstance(self.operands[i], Identifier):
                self.operands[i].build(quantum_evaluator)
        quantum_evaluator.quantum_circuit.x([op.result[-1] for op in self.operands])
        quantum_evaluator.quantum_circuit.mcx([op.result[-1] for op in self.operands], self.result[-1])
        quantum_evaluator.quantum_circuit.x([op.result[-1] for op in self.operands])
        quantum_evaluator.quantum_circuit.x(self.result[-1])

    def reverse(self, quantum_evaluator):
        quantum_evaluator.quantum_circuit.x(self.result[-1])
        quantum_evaluator.quantum_circuit.x([op.result[-1] for op in self.operands])
        quantum_evaluator.quantum_circuit.mcx([op.result[-1] for op in self.operands], self.result[-1])
        quantum_evaluator.quantum_circuit.x([op.result[-1] for op in self.operands])
        for i in range(len(self.operands)):
            if not isinstance(self.operands[i], Identifier):
                self.operands[i].reverse(quantum_evaluator)
            if self.operands[i].needs_result_allocation(): 
                self.operands[i].release_result_qubits(quantum_evaluator) 
    
# --- Register definition AST nodes ---
class RegisterDefinition(ASTNode):
    def __init__(self, line: int, name: str, n: int) -> None:
        """
        :param line: Line of code
        :type line: int
        :param name: Register's label/name
        :type name: str
        :param n: Register's size (number of qubits)
        :type n: int
        """
        super().__init__(line)
        assert isinstance(name, str)
        assert isinstance(n, int)
        self.name = name
        self.n = n

class RegisterExpressionDefinition(RegisterDefinition):
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
        super().__init__(line, name, n)
        assert isinstance(expr, Expression)
        self.expr = expr

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'RegisterExpressionDefinition',
            'name': self.name,
            'size': self.n,
            'expr': self.expr.to_dict()
        }
    
    def build(self, quantum_evaluator):
        """Build the quantum circuit that evaluates the inner expression and asign the result to the target register

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        """
        self.expr.pre_build(quantum_evaluator)
        if self.expr.needs_result_allocation(): self.expr.alloc_result_qubits(quantum_evaluator)
        self.expr.build(quantum_evaluator)
        target = [qbit for qbit in quantum_evaluator.get_qiskit_register(self.name)]
        qunits.register_by_register_addition(quantum_evaluator.quantum_circuit, self.expr.result, target)

    def reverse(self, quantum_evaluator):
        """Build the inverse quantum circuit

        :param quantum_evaluator: Parent quantum evaluator
        :type quantum_evaluator: QuantumEvaluator
        """
        target = [qbit for qbit in quantum_evaluator.get_qiskit_register(self.name)]
        qunits.register_by_register_subtraction(quantum_evaluator.quantum_circuit, self.expr.result, target)
        self.expr.reverse(quantum_evaluator)
        if self.expr.needs_result_allocation(): self.expr.release_result_qubits(quantum_evaluator)

class RegisterSetDefinition(RegisterDefinition):
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
        super().__init__(line, name, n)
        assert all([isinstance(v, int) for v in values])
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
        """
        :param line: Line of code
        :type line: int
        """
        super().__init__(line)

class Amplify(Terminator):
    def __init__(self, line: int, target: str, iterations: int) -> None:
        """
        :param line: Line of code
        :type line: int
        :param target: Label of the target register
        :type target: str
        :param iterations: Number of iterations of the Grover's search algorithm
        :type iterations: int
        """
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
    def __init__(self, line: int, regdefseq: List[RegisterDefinition], terminator: Terminator) -> None:
        """
        :param line: Line of code
        :type line: int
        :param regdefseq: Register definition sequence
        :type regdefseq: List[RegisterDefinition]
        :param terminator: terminator AST node
        :type terminator: Terminator
        """
        super().__init__(line)
        assert isinstance(regdefseq, list)
        assert all([isinstance(x, RegisterDefinition) for x in regdefseq])
        assert isinstance(terminator, Terminator)
        self.regdefseq = regdefseq
        self.terminator = terminator

    def to_dict(self) -> Dict[str, object]:
        return {
            'type': 'FullCode',
            'sequence': [x.to_dict() for x in self.regdefseq],
            'terminator': self.terminator.to_dict()
        }
    
    def get_reg_names_sizes_and_sets(self) -> List[Tuple[str, int, set]]:
        """Return a list with a tuple for each defined register. Each tuple have a label, a size and a set of values.

        :return: List of tuples
        :rtype: List[Tuple[str, int, set]]
        """
        return [(reg.name, reg.n, reg.values) if isinstance(reg, RegisterSetDefinition) else (reg.name, reg.n, None) for reg in self.regdefseq]
    
    def check_definition_errors(self):
        """Check if there are errors of multiple definitions of the same identifier or missing identifier definitions

        :raises SynthError: Identifier already defined
        :raises SynthError: Identifier not defined
        """
        defined_registers = []
        for regdef in self.regdefseq:
            if regdef.name in defined_registers:
                raise SynthError(regdef.line, f'"{regdef.name}" is already defined')
            if isinstance(regdef, RegisterExpressionDefinition):
                for leaf in regdef.expr.get_leafs():
                    if not leaf in defined_registers:
                        raise SynthError(regdef.line, f'The identifier {leaf} is not defined')
            defined_registers.append(regdef.name)

        if isinstance(self.terminator, Amplify):
            if self.terminator.target not in defined_registers:
                raise SynthError(regdef.line, f'The target "{self.terminator.target}" specified at the amplify terminator is not defined')