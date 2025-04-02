import json
from uuid import uuid4
from typer import echo, Option, Exit, Context, Argument, Typer
from zombiotrack.interfaces.cli.utils.data_management import load_state, save_state
from zombiotrack.models.state import ZombieSimulationState
from zombiotrack.models.building import Building
from zombiotrack.interfaces.constants import DEFAULT_FLOORS, DEFAULT_ROOMS_PER_FLOOR
from zombiotrack.use_cases.constants import DO_NOTHING, ZOMBIE_COUNT
from zombiotrack.use_cases.zombie_simulation import ZombieEnvironment

simulation_app = Typer(help="CLI for the Zombie Invasion Simulation")

@simulation_app.command()
def configure(
    floors_count: int = Option(DEFAULT_FLOORS, "--floors-count", "-fc", help="Number of floors in the building"),
    rooms_per_floor: int = Option(DEFAULT_ROOMS_PER_FLOOR, "--rooms-per-floor", "-rpf", help="Number of rooms per floor"),
    infected: list[str] = Option([], "--infected", "-i", help="Initial infected coordinates (format: 'floor,room:count')"),
    config_file: str| None = Option(None, "--config-file", "-c", help="Path to a local JSON configuration file"),
    state_file: str| None = Option(None, "--state-file", help="Path to a state file (overrides session)"),
    session_id: str| None = Option(None, "--session-id", "-s", help="Session ID to use")
) -> str:
    """
    Configures the simulation. If a config_file is provided,
    it overrides the command-line options. If no session_id is provided,
    a new one is generated.
    """
    # If a config file is provided, load values from it.
    if config_file:
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
            floors_count = data.get("floors_count", floors_count)
            rooms_per_floor = data.get("rooms_per_floor", rooms_per_floor)
            infected = data.get("infected", infected)
        except Exception as e:
            echo(f"Error reading config file: {e}")
            raise Exit()

    # Generate a new session id if not provided and no state_file override.
    if not session_id and not state_file:
        session_id = str(uuid4())
        echo(f"Generated new session id: {session_id}")

    building = Building.from_2d_floor_spec(floors_count=floors_count, rooms_per_floor=rooms_per_floor)
    
    # Parse the infected list if any.
    def parse_infected(infected_list: list[str]) -> dict:
        infected_coords = {}
        for item in infected_list:
            try:
                echo(f"Item: {item}")
                coord_part, count_part = item.split(":")
                floor_str, room_str = coord_part.split(",")
                floor = int(floor_str.strip())
                room = int(room_str.strip())
                count = int(count_part.strip())
                infected_coords[(floor, room)] = {ZOMBIE_COUNT: count}
            except Exception as e:
                raise ValueError(f"Invalid format '{item}'. Expected 'floor,room:count'.") from e
        return infected_coords

    initial_infected = parse_infected(infected) if infected else {}
    initial_state = ZombieSimulationState(
        building=building,
        infected_coords=initial_infected,
        last_action="initialization",
        last_action_payload={"infected": initial_infected}
    )
    env = ZombieEnvironment(initial_state)
    # Save the serialized environment (state) to file.
    save_state(session_id, state_file, env.state)
    echo(f"Simulation configured with {floors_count} floors, {rooms_per_floor} rooms.")
    echo(f"Initial infected: {initial_infected}")
    echo(f"Session id: {session_id if session_id else state_file}")
    return session_id

@simulation_app.command()
def step(
    step_action: int = Option(DO_NOTHING, help="Step-level action code (default is DO_NOTHING)"),
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file", resolve_path=True, writable=True)
):
    """
    Advances the simulation by one turn.
    """
    state = load_state(session_id, state_file)
    env = ZombieEnvironment(state)
    env.state = env.step(step_action)
    save_state(session_id, state_file, env.state)
    echo(f"Turn advanced to {env.state.turn}. Last action: {env.state.last_action}")

@simulation_app.command()
def run(
    ctx: Context,
    steps: int = Argument(10, help="Number of steps to run"),
    floors_count: int | None = Option(None, "--floors-count", "-fc", help="Reconfigure with this floor count"),
    rooms_per_floor: int | None = Option(None, "--rooms-per-floor", "-rpf", help="Reconfigure with this room count"),
    infected: list[str] = Option([], "--infected", "-i", help="Reconfigure with initial infected coordinates. (format: 'floor,room:count')"),
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file")
):
    """
    Composite command: Optionally reconfigures the simulation and then runs multiple steps.
    """
    # If any reconfiguration options are provided, call 'configure' and override.
    if floors_count is not None or rooms_per_floor is not None or infected:
        session_id = ctx.invoke(
            configure,
            floors_count=floors_count if floors_count is not None else DEFAULT_FLOORS,
            rooms_per_floor=rooms_per_floor if rooms_per_floor is not None else DEFAULT_ROOMS_PER_FLOOR,
            infected=infected,
            config_file=None,
            state_file=state_file,
            session_id=session_id,
        )
    state = load_state(session_id, state_file)
    env = ZombieEnvironment(state)
    for _ in range(steps):
        env.state = env.step()
    save_state(session_id, state_file, env.state)
    echo(f"Composite run complete. Turn: {env.state.turn}, Last action: {env.state.last_action}")

