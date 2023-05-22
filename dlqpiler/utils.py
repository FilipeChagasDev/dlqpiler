#Filipe Chagas, 2023

from typing import *
from math import sqrt

def is_none(obj) -> bool:
    """
    :param obj: Object or None
    :type obj: Any type
    :return: True if obj is None
    :rtype: bool
    """
    return isinstance(obj, type(None))

def natural_to_binary(x: int, n: int) -> List[bool]:
    """Returns x in the binary system.
    :param x: Natural (including zero) to convert.
    :type x: int
    :param n: Number of bits.
    :type n: int
    :return: List of bits. Each bit is a bool. Most significant bit last.
    :rtype: List[bool]
    """
    assert n > 0
    x = x % 2**n
    return [bool((x//2**i)%2) for i in range(n)]

def binary_to_natural(x: List[bool]) -> int:
    """Returns x as a natural number (including zero).
    :param x: List of bits. Most significant bit last.
    :type x: List[bool]
    :return: Natural number (including zero).
    :rtype: int
    """
    n = len(x)
    return sum([(2**i)*int(x[i]) for i in range(n)])

def set_to_statevector(values: Set[int], size: int) -> List[float]:
    """Return the statevector of a register initialized with a set of positive integer values.

    :param values: Superposed values
    :type values: Set[int]
    :param size: Register's size
    :type size: int
    :return: Statevector as a list of float values
    :rtype: List[float]
    """
    assert all([isinstance(v, int) for v in values])
    assert all([v >= 0 for v in values])
    assert all([v < 2**size for v in values])
    assert isinstance(size, int) and size > 0

    psi = [0 for i in range(2**size)]
               
    for v in values:
        psi[v] = 1/sqrt(len(values))

    return psi