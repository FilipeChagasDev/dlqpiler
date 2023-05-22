#Filipe Chagas, 2023
from typer import Typer
from dlqpiler import synth
from ply import yacc
from qiskit import Aer
import pandas as pd

app = Typer()

def _sim(code: str) -> pd.DataFrame:
    qe = synth.QuantumEvaluator(yacc.parse(code))
    qe.build_all()
    return qe.simulate(Aer.get_backend('aer_simulator'))

def _plot(code: str):
    qe = synth.QuantumEvaluator(yacc.parse(code))
    qe.build_all()
    qe.quantum_circuit.draw(output='mpl')

@app.command()
def sim(codefn: str, destfn: str):
    """Execute a simulation of the given code and save it's results to a xlsx file

    :param codefn: Path to the code file
    :type codefn: str
    :param destfn: Path to the XLSX file
    :type destfn: str
    """
    with open(codefn, 'r') as f:
        code = f.read()
        result = _sim(code)
        result.to_excel(destfn)

@app.command()
def plot(codefn: str):
    """Plot the quantum circuit generated for the given code

    :param codefn: Path to the code file
    :type codefn: str
    """
    with open(codefn, 'r') as f:
        code = f.read()
        _plot(code)