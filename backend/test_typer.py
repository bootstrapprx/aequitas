import typer
app = typer.Typer()

@app.command()
def test(name: str = typer.Option(..., "-n")):
    print(name)

if __name__ == "__main__":
    app()
