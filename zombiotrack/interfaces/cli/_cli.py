from typer import Typer
from .control import simulation_app
from .visualization import visualization_app
from .interactive import menu_app

app = Typer(help="CLI for the Zombie Invasion Simulation")
app.add_typer(simulation_app, name="simulate")
app.add_typer(visualization_app, name="visualize")
app.add_typer(menu_app, name="interactive")


if __name__ == "__main__":
    app()
