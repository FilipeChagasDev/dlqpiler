# DLQpiler

DLQpiler is a compiler of the DLQ language (Declarative Language for Quantum). Both the compiler and the language are part of my bachelor's thesis in Computer Engineering (in Brazil we call TCC, which is a portuguese acronym for end-of-course work). DLQ is, as the name suggests, a high-level declarative language of abstraction that is translated into quantum circuits by the compiler. The grammar of this language is context-free, consisting of immutable variables, arithmetic operators, relational operators, logic operators, and statements specific to quantum algorithms. The DLQpiler compiler is written in Python, based on the PLY library and the Qiskit SDK. This compiler generates quantum circuits for the IBM Quantum Experience platform.


For now, the most detailed documentation of the project is my monograph in Portuguese, which is yet to be published in UFMT's virtual library. Soon I will post articles in Portuguese and English about this project.

## How to use

First, you must install the compiler. You can do this using the following command:

```
pip install .
```

Remember that the **dlqpiler** directory must be your working directory in the terminal for this command to work.

Dlqpiler is a just-in-time (JIT) compiler. To compile and simulate a code, you must write it to a text file and execute the command `dlqpiler sim <codefile> <outfile> <nshots>` , where `<codefile>` is the path to the code file, `<outfile>` is the path to the output XLSX file (remember to put the ".xlsx" extension), and `<nshots>` is the number of simulation shots. This command uses Qiskit's statevector simulator. You can also plot the quantum circuit resulting from compiling a code using the `dlqpiler plot <codefile>` command.

Note that when executing code, errors can occur that are not handled very well (especially if they are syntax errors). So if you get a strange error when executing a DLQpiler command, check the syntax correctness of your code. Feel free to create issues reporting problems in this repository, and also to create forks with improvements for this project.

## Language Overview

The current version (1.0.0) of the DLQ language is dedicated to solving satisfiability problems of simple expressions composed of logical, arithmetic and relational operators. It is possible to solve problems like Boolean satisfiability, prime factoring, and solving systems of equations. In the examples directory of this repository there are two examples of code with results, which serve as a proof of concept for the project. However, there are still technical problems (bugs) with the code that need to be investigated and fixed. Also, the use of this compiler is still restricted to the **aer_simulator**, as there are no features for correction and mitigation of errors due to the quantum decoherence of the NISQ computers. 

The syntax of the language is composed of the following elements:

* **Variables** - mathematical symbols defined in terms of relevance sets or expressions. A variable in DLQ is immutable and does not necessarily have a defined value until the program is run, but has a set of possible values. The syntax of defining a variable is as follows:
    * as set: ``<name> [<size>] := {<number>, <number>, ..., <number>};``. where ``<name>`` is the variable name, ``<size>`` is the variable size in number of qubits, and ``<number>`` is a natural number. In this type of declaration, the variable is defined as belonging to a closed set of natural numbers. This will result in a quantum register initialized as a superposition of the values of the set.
    * as expression: ``<name> [<size>] := <expression>;`` In this case, the value of the variable is defined as an expression that depends on other variables that are already defined. In the compilation process, this is translated into a quantum register that is used by the quantum oracle of Grover's algorithm to store the result of the expression. 

* **Operators with one or two operands** - are the symbols that compose the expressions, and can be logical, arithmetic, and relational. Currently, the following operators are available:
  * Logical not: ``not <expression>``
  * Logical or: ``<expression> or <expression>``
  * Logical and: ``<expression> and <expression>``
  * Addition: ``<expression> + <expression>``
  * Subtraction: ``<expression> - <expression>``
  * Product: ``<expression> * <expression>``
  * Power: ``<expression> ^ <number>`` (only constant exponents allowed)
  * Equal: ``<expression> = <expression>``
  * Not-equal: ``<expression> != <expression>``
  * Less-than: ``<expression> < <expression>``
  * Greater-than: ``<expression> > <expression>``

* **Terminators** - is the final sentence of the code, which defines how the problem should be solved. Currently there is only one terminator: **amplify**. This terminator has the syntax ``amplify <name> <number> times``, where ``<name>`` is the name of the binary variable that is used as the search conditional, and ``<number>`` is the number of iterations of Grover's algorithm.

The general structure of a DLQ program goes something like this:

```
<name1_1> [<size1_1>] := {<number>, <number>, ..., <number>}; 
<name1_2> [<size1_2>] := {<number>, <number>, ..., <number>};
...
<name1_N> [<size1_N>] := {<number>, <number>, ..., <number>};

<name2_1> [<size2_1>] := <expression>;
<name2_2> [<size2_2>] := <expression>;
...
<name2_N> [<size2_N>] := <expression>;

<bin_var_name> [1] := <expression>;

amplify <bin_var_name> <n_iterations> times
```

Pay attention to the following detail: **there is no semicolon after the terminator!**

## Examples

### Boolean satisfiability

The Boolean satisfiability problem consists in checking whether a Boolean expression is satisfiable. The following code in DLQ finds the solution of the expression $(x_1 \vee \neg x_3 \vee x_4) \wedge (\neg x_2 \vee x_3 \vee \neg x_4)$.

```
x1[1] in {false, true};
x2[1] in {false, true};
x3[1] in {false, true};
x4[1] in {false, true};
y[1] := (x1 or not x3 or x4) and (not x2 and x3 and not x4);
amplify y 3 times
```

From this code, a quantum Grover search circuit with 3 iterations will be generated to search for the solution of the Boolean expression presented above. 

The result obtained in the simulation of this code is as follows:

| |x1|x2|x3|x4|y|$freq|
|:----|:----|:----|:----|:----|:----|:----|
|0|1|0|1|0|1|914|
|1|1|0|1|1|0|13|
|2|1|1|1|1|0|13|
|3|0|1|1|0|0|11|
|4|1|0|0|1|0|9|
|5|0|0|0|0|0|8|
|6|0|0|0|1|0|8|
|7|1|1|0|0|0|7|
|8|1|1|1|0|0|7|
|9|1|1|0|1|0|7|
|10|0|1|1|1|0|7|
|11|0|0|1|1|0|6|
|12|0|1|0|1|0|6|
|13|0|1|0|0|0|4|
|14|1|0|0|0|0|2|
|15|0|0|1|0|0|2|

Notice that in the 1024 simulation shots, the solution of the Boolean expression is obtained with 91% relative frequency.

## Prime factorization

The prime factorization problem consists in finding, for any integer $x$, a pair of prime numbers $(p_1, p_2)$ such that $p_1 p_2 = x$. The DLQ code for solving this problem, considering $x=15$, is as follows:

```
p1[4] in {2, 3, 5, 7};
p2[4] in {2, 3, 5, 7};
y[1] := p1*p2=15;
amplify y 2 times
```

From this code, a quantum Grover search circuit with 2 iterations will be generated to search for the solution of the expression ``p1*p2=15``. 

The simulation result of this code, with 1024 shots, is as follows:

| |p1|p2|y|$freq|
|:----|:----|:----|:----|:----|
|0|5|3|1|469|
|1|3|5|1|467|
|2|5|2|0|11|
|3|2|3|0|8|
|4|7|7|0|8|
|5|7|3|0|8|
|6|7|5|0|7|
|7|7|2|0|7|
|8|3|7|0|6|
|9|5|7|0|6|
|10|5|5|0|6|
|11|2|2|0|5|
|12|2|7|0|5|
|13|2|5|0|5|
|14|3|3|0|4|
|15|3|2|0|2|

## Grammar

The DLQ language has the following context-free grammar in the Backus-Naur form:

```
<fullcode> ::= <regdefseq> <amplifyterm>
<amplifyterm> ::= "amplify" ID NUMBER "times"
<regdefseq> ::= <regdef> ";" <regdefseq> | <regdef> ";"
<regdef> ::= <regdefs> | <regdefx>
<regdefs> ::= ID "[" NUMBER "]" "in" "{" <expseq> "}"
<regdefx> ::= ID "[" NUMBER "]" ":=" <expression>
<expseq> ::= <expseq> "," <expression> | <expression>
<expression> ::= <expression> "or" <expression>
             | <expression> "and" <expression>
             | "not" <expression>
             | <expression> "=" <expression>
             | <expression> "!=" <expression>
             | <expression> "<" <expression>
             | <expression> ">" <expression>
             | <expression> "+" <expression>
             | <expression> "-" <expression>
             | <expression> "*" <expression>
             | <expression> "^" <expression>
             | <expression> "/" <expression>
             | "-" <expression> (unary minus)
             | "(" <expression> ")"
             | "false"
             | "true"
             | NUMBER
             | ID
```

The precedence table of this grammar is as follows:

|Priority|Operators|Associativity|
|:----|:----|:----|
|9ª|or|left|
|8ª|and|left|
|7ª|not|right|
|6ª|<, >|left|
|5ª|=, !=|left|
|4ª|+, -|left|
|3ª|*, /|left|
|2ª|- (unary minus)|right|
|1ª|^|right|

The regular expressions are as follows:

|Name|Regex|
|:----|:----|
|NUMBER|[0-9]+|
|ID|[a-zA-Z_][a-zA-Z_0-9]*|