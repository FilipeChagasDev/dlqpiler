from typer import Typer

app = Typer()

#This is just a test code
@app.command()
def hello():
    print("Hello.")

@app.command()
def bye(name: str):
    print(f"Bye {name}")