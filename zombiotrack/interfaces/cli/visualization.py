import json
from rich.table import Table
from rich.console import Console
from typer import Option, echo, Typer
from zombiotrack.interfaces.cli.utils.data_management import load_state

visualization_app = Typer(help="Command group for visualization porpouses")

def get_color(sensor_status: str, blocked: bool = False) -> str:
    """
    Determines the style based on the sensor status and zombie count.
    Uses the sensor status from the room to set the base color.
    For example, if sensor is "alert", use red; otherwise green.
    """
    if blocked:
        return "blue"
    base = "green" if sensor_status.lower() != "alert" else "red"
    return f"bold {base}"

@visualization_app.command()
def grid(
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file")
):
    """
    Loads the simulation state and displays a grid visualization.
    Each row represents a floor and each column a room.
    Each cell shows the zombie count styled according to the room's sensor status
    and the zombie count.
    """
    state = load_state(session_id, state_file)
    # Use model attributes for type-safety:
    building = state.building  # instance of Building
    floors = building.floors   # assumed to be a list of Floor objects
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
def show_state(
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file"),
    json_path: str = Option("$", "--json-path", help="Path to a key in the state JSON")
):
    """
    Displays the current simulation state.
    """
    state = load_state(session_id, state_file)
    json_state = state.model_dump_json(indent=2)
    path_parts = json_path.split(".") if json_path else []
    for part in path_parts:
        if part == "$":
            continue
        json_state = json.dumps(json.loads(json_state).get(part, {}), indent=2)
    echo(json_state)