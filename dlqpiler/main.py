#Filipe Chagas, 2023
from typer import Typer
from dlqpiler import synth
from dlqpiler import parser
from ply import yacc
from qiskit import Aer
import pandas as pd
from matplotlib import pyplot as plt

app = Typer()

def psim(code: str, shots: int) -> pd.DataFrame:
    qe = synth.QuantumEvaluator(yacc.parse(code))
    qe.build_all()
    return qe.simulate(Aer.get_backend('aer_simulator'), shots=shots)

def pplot(code: str):
    qe = synth.QuantumEvaluator(yacc.parse(code))
    qe.build_all()
    qe.quantum_circuit.draw(output='mpl')
    plt.show()

def get_qqc(code: str):
    qe = synth.QuantumEvaluator(yacc.parse(code))
    qe.build_all()
    return qe.quantum_circuit

@app.command()
def sim(codefn: str, destfn: str, shots: int):
    """Execute a simulation of the given code and save it's results to a xlsx file

    :param codefn: Path to the code file
    :type codefn: str
    :param destfn: Path to the XLSX file
    :type destfn: str
    :param shots: Number of simulation shots
    :type shots: int
    """
    with open(codefn, 'r') as f:
        code = f.read()
        result = psim(code, shots)
        result.to_excel(destfn)

@app.command()
def plot(codefn: str):
    """Plot the quantum circuit generated for the given code

    :param codefn: Path to the code file
    :type codefn: str
    """
    with open(codefn, 'r') as f:
        code = f.read()
        pplot(code)