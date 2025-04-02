# zombiotrack/interfaces/cli/menu.py
from json import dumps
from typer import Option, Context, Typer, echo, prompt
from zombiotrack.interfaces.cli.control import fallback_config
from zombiotrack.interfaces.cli.utils.data_management import load_state
from zombiotrack.use_cases.zombie_simulation import ZombieEnvironment
from rich.console import Console
from zombiotrack.interfaces.cli.visualization import render_grid
from re import match

menu_app = Typer()
console = Console()


def prompt_int(prompt_msg: str, min_value: int = 0) -> int:
    """
    Prompt the user until a valid non-negative integer is entered.

    This utility function is used for safe integer input from the user,
    with optional enforcement of a minimum value.

    Parameters
    ----------
    prompt_msg : str
        The message to display to the user when prompting.
    min_value : int, optional
        The minimum allowed value (default is 0).

    Returns
    -------
    int
        A valid integer value provided by the user.
    """

    while True:
        try:
            value = int(prompt(prompt_msg))
            if value < min_value:
                console.print("[red]Value must be non-negative.[/red]")
                continue
            return value
        except ValueError:
            console.print("[red]Invalid input. Enter a valid number.[/red]")


@menu_app.command("run")
def interactive(
    ctx: Context,
    floors_count: int | None = Option(
        None, "--floors-count", "-fc", help="Reconfigure with this floor count"
    ),
    rooms_per_floor: int | None = Option(
        None, "--rooms-per-floor", "-rpf", help="Reconfigure with this room count"
    ),
    infected: list[str] = Option(
        [],
        "--infected",
        "-i",
        help="Reconfigure with initial infected coordinates. (format: 'floor,room:count')",
    ),
    session_id: str | None = Option(None, "--session-id", "-s"),
    state_file: str | None = Option(None, "--state-file"),
):
    """
    Launch an interactive simulation control loop via a terminal menu.

    Allows the user to manually step through simulation turns, view the building grid,
    modify rooms, reset the simulation, or exit. Optionally accepts configuration inputs
    or falls back to a prompt-driven setup if not enough parameters are provided.

    Parameters
    ----------
    ctx : Context
        The Typer CLI context for dispatching to other commands.
    floors_count : int, optional
        Number of floors to configure (if starting from scratch).
    rooms_per_floor : int, optional
        Number of rooms per floor (if starting from scratch).
    infected : list of str, optional
        List of infected coordinates in format 'floor,room:count'.
    session_id : str, optional
        Session ID to resume from, if provided.
    state_file : str, optional
        Path to a saved state file to resume from.

    Returns
    -------
    None
        The loop runs until the user selects "Exit". Simulation state is updated in memory.
    """

    if not (rooms_per_floor and floors_count) and (
        session_id is None and state_file is None
    ):
        echo("Building config not provided, please answer how to start the simulation")
        floors_count = (
            int(prompt("Floor Count")) if floors_count is None else floors_count
        )
        rooms_per_floor = (
            int(prompt("Rooms per Floor"))
            if rooms_per_floor is None
            else rooms_per_floor
        )

    if not infected and (session_id is None and state_file is None):
        echo("Provide infected population")
        while True:
            console.print("\n[bold cyan]--- Initial infection ---[/bold cyan]")
            console.print("1. Add initial zombies 🧟")
            console.print("Any. Done ✅")

            option = prompt("\nSelect an option")

            if option == "1":
                room, floor = (None, None)
                quantity: int | None = None
                echo("Replace zombies at location.")
                while room is None or floor is None:
                    user_input: str = prompt(
                        "Select a Floor and Room. (format: 'floor,room')"
                    )
                    if match(r"^(\d,\d)$", user_input):
                        room, floor = user_input.split(",")
                while quantity is None:
                    user_input: str = prompt(
                        "How much zombies do you want on that location?"
                    )
                    if user_input.isdigit() and int(user_input) >= 0:
                        quantity = int(user_input)
                infected.append(f"{floor},{room}:{quantity}")
                echo(f"Current zombie configuration: {dumps(infected)}")
            else:
                break

    if not session_id and not state_file:
        session_id = fallback_config(
            ctx=ctx,
            floors_count=floors_count,
            rooms_per_floor=rooms_per_floor,
            infected=infected,
            state_file=state_file,
            session_id=session_id,
        )

    state = load_state(session_id, state_file)
    env = ZombieEnvironment(state)

    while True:
        console.print("\n[bold cyan]--- ZOMBIE SIMULATION MENU ---[/bold cyan]")
        console.print("1. Advance turn 🧟")
        console.print("2. Show building state 🏢")
        console.print("3. Clean a room 🧼")
        console.print("4. Manage room access 🚪")
        console.print("5. Reset a sensor 🔁")
        console.print("6. Reset simulation 💥")
        console.print("7. Exit ❌")

        option = prompt("\nSelect an option").strip()

        if option == "1":
            env.state = env.step()
            console.print("[green]Turn advanced.[/green]")

        elif option == "2":
            render_grid(env.state)

        elif option in {"3", "4", "5"}:
            floor = prompt_int("Floor number")
            room = prompt_int("Room number")

            try:
                if option == "3":
                    env.clean_room(floor, room)
                    console.print(f"[green]Room ({floor},{room}) cleaned.[/green]")
                elif option == "4":
                    console.print("\n[bold cyan]--- Room Access Menu ---[/bold cyan]")
                    console.print("1. Block room 🚪")
                    console.print("2. Unblock room 🔓")
                    sub_option = prompt("Select an option").strip()

                    try:
                        if sub_option == "1":
                            env.state = env.block_room(floor, room)
                            console.print(
                                f"[yellow]Room ({floor},{room}) blocked.[/yellow]"
                            )
                        elif sub_option == "2":
                            env.state = env.unblock_room(floor, room)
                            console.print(
                                f"[cyan]Room ({floor},{room}) unblocked.[/cyan]"
                            )
                        else:
                            console.print("[red]Invalid sub-option.[/red]")
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                elif option == "5":
                    env.reset_sensor(floor, room)
                    console.print(
                        f"[blue]Sensor in room ({floor},{room}) reset.[/blue]"
                    )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif option == "6":
            console.print(
                "\n💥 [bold red]NUKING the simulation... Resetting to zero.[/bold red] 💥"
            )
            env.reset_simulation(infected_coords=state.infected_coords)
            console.print("[green]Simulation has been reset.[/green]")

        elif option == "7":
            console.print("[yellow]Exiting interactive mode.[/yellow]")
            break

        else:
            console.print("[red]Invalid option. Try again.[/red]")

        render_grid(env.state)
