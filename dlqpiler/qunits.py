#Filipe Chagas, 2023

import qiskit
from itertools import product
from dlqpiler.utils import natural_to_binary
from math import *
from typing import *

def qft(n: int) -> qiskit.circuit.Gate:
    """Returns a QFT gate for n qubits.

    :param n: Number of target qubits.
    :type n: int
    :return: QFT gate.
    :rtype: qiskit.circuit.Gate
    """
    def rotations(my_circuit: qiskit.circuit.Gate, m: int):
        if m == 0:
            return my_circuit
        else:
            my_circuit.h(m-1) #Add a Haddamard gate to the most significant qubit
        
            for i in range(m-1):
                my_circuit.crz(pi/(2**(m-1-i)), i, m-1)

            rotations(my_circuit, m-1) 
    
    my_circuit = qiskit.QuantumCircuit(n, name='QFT')
    
    rotations(my_circuit, n)

    for m in range(n//2):
        my_circuit.swap(m, n-m-1)

    return my_circuit.to_gate()

# --- Arithmetic circuits ---

def register_by_constant_addition(n: int, c: int) -> qiskit.circuit.Gate:
    """
    Register-by-constant addition gate (simplified draper adder).
    Get a gate to perform an addition of a constant $c$ to a integer register.
    No ancillary qubits needed.

    :param n: Number of target qubits.
    :type n: int
    :param c: Constant to add.
    :type c: int
    :return: RCA gate.
    :rtype: qiskit.circuit.Gate
    """
    assert n > 0

    my_circuit = qiskit.QuantumCircuit(n, name=f'$U_+({c})$')

    my_qft = qft(n)
    my_circuit.append(my_qft, list(range(n)))

    for i in range(n):
        theta = c * (pi / (2**(n-i-1)))
        my_circuit.rz(theta, i)

    my_circuit.append(my_qft.inverse(), list(range(n)))

    return my_circuit.to_gate()

def register_by_register_addition(circ: qiskit.QuantumCircuit, src_reg: List[qiskit.circuit.Qubit], target_reg: List[qiskit.circuit.Qubit]):
    """Build a register-by-register addition circuit

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param src_reg: Operand register
    :type src_reg: List[qiskit.circuit.Qubit]
    :param target_reg: Target register
    :type target_reg: List[qiskit.circuit.Qubit]
    """
    for i in range(len(src_reg)):
        controlled_addition = register_by_constant_addition(len(target_reg), 2**i).control(1)
        circ.append(controlled_addition, [src_reg[i]]+target_reg)

def register_by_register_addition_dg(circ: qiskit.QuantumCircuit, src_reg: List[qiskit.circuit.Qubit], target_reg: List[qiskit.circuit.Qubit]):
    """Build an inverse register-by-register addition circuit

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param src_reg: Operand register
    :type src_reg: List[qiskit.circuit.Qubit]
    :param target_reg: Target register
    :type target_reg: List[qiskit.circuit.Qubit]
    """
    for i in range(len(src_reg))[::-1]:
        controlled_addition = register_by_constant_addition(len(target_reg), 2**i).inverse().control(1)
        circ.append(controlled_addition, [src_reg[i]]+target_reg)

def register_by_register_subtraction(circ: qiskit.QuantumCircuit, src_reg: List[qiskit.circuit.Qubit], target_reg: List[qiskit.circuit.Qubit]):
    """Build a register-by-register subtraction circuit

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param src_reg: Operand register
    :type src_reg: List[qiskit.circuit.Qubit]
    :param target_reg: Target register
    :type target_reg: List[qiskit.circuit.Qubit]
    """
    for i in range(len(src_reg)):
        controlled_addition = register_by_constant_addition(len(target_reg), -2**i).control(1)
        circ.append(controlled_addition, [src_reg[i]]+target_reg)

def register_by_register_subtraction_dg(circ: qiskit.QuantumCircuit, src_reg: List[qiskit.circuit.Qubit], target_reg: List[qiskit.circuit.Qubit]):
    """Build an inverse register-by-register subtraction circuit

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param src_reg: Operand register
    :type src_reg: List[qiskit.circuit.Qubit]
    :param target_reg: Target register
    :type target_reg: List[qiskit.circuit.Qubit]
    """
    for i in range(len(src_reg))[::-1]:
        controlled_addition = register_by_constant_addition(len(target_reg), -2**i).inverse().control(1)
        circ.append(controlled_addition, [src_reg[i]]+target_reg)

def multiproduct(circ: qiskit.QuantumCircuit, bases: List[List[qiskit.circuit.Qubit]], exponents: List[int], result: List[qiskit.circuit.Qubit], constant: int = 1):
    """Build a circuit that perform a productory with constant exponents 

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param bases: List of registers that contains base values
    :type bases: List[List[qiskit.circuit.Qubit]]
    :param exponents: List of exponents
    :type exponents: List[int]
    :param result: Target register
    :type result: List[qiskit.circuit.Qubit]
    :param constant: Constant factor, defaults to 1
    :type constant: int, optional
    """
    #The powers and the productory must be calculated as a sequence of controlled const additions
    factors_indexes = [] #This list contains a sequence with the index of each factor E times, where E is the respective exponent
    for i in range(len(exponents)):
        factors_indexes += [i]*exponents[i]
    
    for t in product(*[list(range(len(bases[factors_indexes[i]]))) for i in range(len(factors_indexes))]): #Each tuple t have the indexes of the qubits that must be used as control of each register
        ctrl_idx = {factor_index:set() for factor_index in range(len(bases))} #This dict will map each factor's index to a set with it's control qubit's indexes
        #fill the ctrl dict
        for i in range(len(t)): 
            ctrl_idx[factors_indexes[i]].add(t[i])

        ctrl_qubits = [] #Control qubits
        #fill the ctrl_qubits list 
        for factor_index in ctrl_idx.keys():
            for qubit_index in ctrl_idx[factor_index]:
                ctrl_qubits.append(bases[factor_index][qubit_index])

        c = constant*2**sum(t) #Constant to add

        #Append controled const addition
        my_const_adder = register_by_constant_addition(len(result), c)
        my_const_adder = my_const_adder.control(len(ctrl_qubits))
        circ.append(my_const_adder, ctrl_qubits + result)


def multiproduct_dg(circ: qiskit.QuantumCircuit, bases: List[List[qiskit.circuit.Qubit]], exponents: List[int], result: List[qiskit.circuit.Qubit], constant: int = 1):
    """Build the inverse product circuit 

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param bases: List of registers that contains base values
    :type bases: List[List[qiskit.circuit.Qubit]]
    :param exponents: List of exponents
    :type exponents: List[int]
    :param result: Target register
    :type result: List[qiskit.circuit.Qubit]
    :param constant: Constant factor, defaults to 1
    :type constant: int, optional
    """
    #The powers and the productory must be calculated as a sequence of controlled const additions
    factors_indexes = [] #This list contains a sequence with the index of each factor E times, where E is the respective exponent
    for i in range(len(exponents)):
        factors_indexes += [i]*exponents[i]

    instructions = []
    
    for t in product(*[list(range(len(bases[factors_indexes[i]]))) for i in range(len(factors_indexes))]): #Each tuple t have the indexes of the qubits that must be used as control of each register
        ctrl_idx = {factor_index:set() for factor_index in range(len(bases))} #This dict will map each factor's index to a set with it's control qubit's indexes
        #fill the ctrl dict
        for i in range(len(t)): 
            ctrl_idx[factors_indexes[i]].add(t[i])

        ctrl_qubits = [] #Control qubits
        #fill the ctrl_qubits list 
        for factor_index in ctrl_idx.keys():
            for qubit_index in ctrl_idx[factor_index]:
                ctrl_qubits.append(bases[factor_index][qubit_index])

        c = constant*2**sum(t) #Constant to add

        #Append controled const addition
        my_const_adder = register_by_constant_addition(len(result), -c)
        my_const_adder = my_const_adder.control(len(ctrl_qubits))
        instructions.append((my_const_adder, ctrl_qubits + result))

    for ins, qbts in instructions[::-1]:
        circ.append(ins, qbts)

# --- Relational circuits ---

def register_less_than_register(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the quantum circuit of the less-than operation

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubit
    :type aux: qiskit.circuit.Qubit
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xleft = left + aux
    register_by_register_subtraction(circ, right, xleft)
    circ.cx(aux, result)
    register_by_register_subtraction_dg(circ, right, xleft)

def register_less_than_register_dg(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the inverse quantum circuit of the less-than operation

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubit
    :type aux: qiskit.circuit.Qubit
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xleft = left + aux
    register_by_register_addition(circ, right, xleft)
    circ.cx(aux, result)
    register_by_register_addition_dg(circ, right, xleft)

def register_greater_than_register(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: qiskit.circuit.Qubit, result: qiskit.circuit.Qubit):
    """Build the quantum circuit of the greater-than operation

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubit
    :type aux: qiskit.circuit.Qubit
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_less_than_register(circ, right, left, aux, result)

def register_greater_than_register_dg(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: qiskit.circuit.Qubit, result: qiskit.circuit.Qubit):
    """Build the inverse quantum circuit of the greater-than operation

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubit
    :type aux: qiskit.circuit.Qubit
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_less_than_register_dg(circ, right, left, aux, result)

def register_less_than_constant(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the quantum circuit of the less-than operation with an constant right operand

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: left operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: right operand
    :type constant: int
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xreg = reg + aux
    adder = register_by_constant_addition(len(xreg), -constant)
    circ.append(adder, xreg)
    circ.cx(reg[-1], result)
    circ.append(adder.inverse(), xreg)

def register_less_than_constant_dg(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the inverse quantum circuit of the less-than operation with an constant right operand

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: left operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: right operand
    :type constant: int
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xreg = reg + aux
    adder = register_by_constant_addition(len(xreg), -constant)
    circ.append(adder.inverse(), xreg)
    circ.cx(reg[-1], result)
    circ.append(adder, xreg)

def register_greater_than_constant(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the quantum circuit of the greater-than operation with an constant right operand

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: left operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: right operand
    :type constant: int
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xreg = reg + aux
    adder = register_by_constant_addition(len(xreg), -constant-1)
    circ.append(adder, xreg)
    circ.cx(reg[-1], result)
    circ.x(result)
    circ.append(adder.inverse(), xreg)

def register_greater_than_constant_dg(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build the inverse quantum circuit of the greater-than operation with an constant right operand

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: left operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: right operand
    :type constant: int
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    xreg = reg + aux
    adder = register_by_constant_addition(len(xreg), -constant-1)
    circ.append(adder.inverse(), xreg)
    circ.x(result)
    circ.cx(reg[-1], result)
    circ.append(adder, xreg)
    
def register_equal_register(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build a quantum circuit to the Equal operation between two registers

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    if len(left) >= len(right):
        xleft = left
        xright = right + aux
    else:
        xleft = left + aux
        xright = right
    assert len(xleft) == len(xright)

    for i in range(len(xleft)):
        circ.cx(xleft[i], xright[i])

    circ.mcx(xright, result)
    
    for i in range(len(xleft))[::-1]:
        circ.cx(xleft[i], xright[i])

def register_equal_register_dg(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build an inverse quantum circuit to the Equal operation between two registers

    :param circ: Target quantum circuit
    :type circ: qiskit.QuantumCircuit
    :param left: left operand
    :type left: List[qiskit.circuit.Qubit]
    :param right: right operand
    :type right: List[qiskit.circuit.Qubit]
    :param aux: ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_equal_register(circ, left, right, aux, result)

def register_equal_constant(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build a quantum circuit to the Equal operation between a register and a constant

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    xreg = reg + aux
    bconst = natural_to_binary(constant, len(reg)+len(aux))
    for i in range(len(bconst)):
        if not bconst[i]:
            circ.x(xreg[i])
    circ.mcx(reg+aux, result)
    for i in range(len(bconst)):
        if not bconst[i]:
            circ.x(xreg[i])

def register_equal_constant_dg(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build an inverse quantum circuit to the Equal operation between a register and a constant

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_equal_constant(circ, reg, constant, aux, result)

def register_not_equal_register(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build a quantum circuit to the Not-Equal operation between two registers

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_equal_register(circ, left, right, aux, result)
    circ.x(result)

def register_not_equal_register_dg(circ: qiskit.QuantumCircuit, left: List[qiskit.circuit.Qubit], right: List[qiskit.circuit.Qubit], aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build an inverse quantum circuit to the Not-Equal operation between two registers

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    circ.x(result)
    register_equal_register_dg(circ, left, right, aux, result)

def register_not_equal_constant(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build a quantum circuit to the Not-Equal operation between a register and a constant

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    register_equal_constant(circ, reg, constant, aux, result)
    circ.x(result)

def register_not_equal_constant_dg(circ: qiskit.QuantumCircuit, reg: List[qiskit.circuit.Qubit], constant: int, aux: List[qiskit.circuit.Qubit], result: qiskit.circuit.Qubit):
    """Build an inverse quantum circuit to the Not-Equal operation between a register and a constant

    :param circ: Target circuit
    :type circ: qiskit.QuantumCircuit
    :param reg: Register operand
    :type reg: List[qiskit.circuit.Qubit]
    :param constant: Const operand
    :type constant: int
    :param aux: Ancilla qubits
    :type aux: List[qiskit.circuit.Qubit]
    :param result: Result qubit
    :type result: qiskit.circuit.Qubit
    """
    circ.x(result)
    register_equal_constant_dg(circ, reg, constant, aux, result)
