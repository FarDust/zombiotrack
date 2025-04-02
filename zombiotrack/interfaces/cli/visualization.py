import json
from rich.table import Table
from rich.console import Console
from typer import Option, echo, Typer
from zombiotrack.interfaces.cli.utils.data_management import load_state
from zombiotrack.models.state import ZombieSimulationState

visualization_app = Typer(help="Command group for visualization porpouses")


def get_color(sensor_status: str, blocked: bool = False) -> str:
    """
    Determine the display style based on sensor status and blocked state.

    If the room is blocked, the style will be blue regardless of the sensor.
    Otherwise, the style will be bold green for normal sensors and bold red for alert sensors.

    Parameters
    ----------
    sensor_status : str
        The current status of the sensor ("normal" or "alert").
    blocked : bool, optional
        Whether the room is blocked. If True, overrides sensor status with blue.

    Returns
    -------
    str
        A style string (e.g., "bold red", "bold green", or "blue") suitable for Rich styling.
    """
    if blocked:
        return "blue"
    base = "green" if sensor_status.lower() != "alert" else "red"
    return f"bold {base}"


def render_grid(state: ZombieSimulationState) -> None:
    """
    Render the current building state as a colored grid in the console.

    Each row of the grid represents a floor, and each column a room.
    The zombie count is displayed in each cell, and the color is determined
    by the sensor status and whether the room is blocked:

    - "alert" → bold red
    - "normal" → bold green
    - blocked rooms → blue (with zombie count shown in brackets)

    Parameters
    ----------
    state : ZombieSimulationState
        The current state of the simulation, containing building layout,
        infection data, and sensor status.

    Returns
    -------
    None
        This function outputs the table directly to the console using Rich.
    """
    building = state.building  # instance of Building
    floors = building.floors  # assumed to be a list of Floor objects
    infected = state.infected_coords  # keys are now tuples thanks to the validator

    table = Table(title="Zombie Simulation Grid", show_lines=True)
    table.add_column("Floor", justify="center")
    # Assume each floor has the same rooms; get room numbers from the first floor.
    if floors:
        first_floor = floors[0]
        room_numbers = [room for room in first_floor.rooms]
    else:
        room_numbers = []
    for rn in room_numbers:
        table.add_column(f"Room {rn}", justify="center")

    for floor in floors.values():
        row = [str(floor.floor_number)]
        for room in floor.rooms.values():
            key = (floor.floor_number, room.room_number)
            info = infected.get(key, {})
            zombie_count = info.get("zombie_count", 0)
            sensor_status = room.sensor.status  # directly from the Room's sensor
            style = get_color(sensor_status, blocked=room.blocked)
            final_text = f"{zombie_count}"
            if room.blocked:
                final_text = f"[{zombie_count}]"
            cell_text = f"[{style}]{final_text}[/{style}]"
            row.append(cell_text)
        table.add_row(*row)

    Console().print(table)


@visualization_app.command()
def grid(
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file"),
):
    """
    Display a colored grid visualization of the simulation state.

    Loads the simulation state from a file or session ID and renders
    a table showing zombie distribution, sensor status, and blocked rooms.

    Parameters
    ----------
    session_id : str, optional
        ID of the session folder to load the simulation state from.
    state_file : str, optional
        Path to a custom state file to load. Takes precedence over session_id.

    Returns
    -------
    None
        Outputs the grid to the console using Rich.
    """
    state = load_state(session_id, state_file)
    # Use model attributes for type-safety:
    render_grid(state)


@visualization_app.command()
def show_state(
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file"),
    json_path: str = Option("$", "--json-path", help="Path to a key in the state JSON"),
):
    """
    Display the raw simulation state or a specific JSON subpath.

    Loads the current simulation state from file or session ID and prints
    the full JSON structure or a subset defined by a dot-separated JSON path.

    Parameters
    ----------
    session_id : str, optional
        ID of the session to load the simulation state from.
    state_file : str, optional
        Path to a specific state file. Overrides session_id if provided.
    json_path : str, optional
        Dot-separated path to a key within the JSON object.
        Defaults to "$" for the full state.

    Returns
    -------
    None
        Prints the selected portion of the state as formatted JSON.
    """
    state = load_state(session_id, state_file)
    json_state = state.model_dump_json(indent=2)
    path_parts = json_path.split(".") if json_path else []
    for part in path_parts:
        if part == "$":
            continue
        json_state = json.dumps(json.loads(json_state).get(part, {}), indent=2)
    echo(json_state)
