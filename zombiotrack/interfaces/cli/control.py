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
    floors_count: int = Option(
        DEFAULT_FLOORS, "--floors-count", "-fc", help="Number of floors in the building"
    ),
    rooms_per_floor: int = Option(
        DEFAULT_ROOMS_PER_FLOOR,
        "--rooms-per-floor",
        "-rpf",
        help="Number of rooms per floor",
    ),
    infected: list[str] = Option(
        [],
        "--infected",
        "-i",
        help="Initial infected coordinates (format: 'floor,room:count')",
    ),
    config_file: str | None = Option(
        None, "--config-file", "-c", help="Path to a local JSON configuration file"
    ),
    state_file: str | None = Option(
        None, "--state-file", help="Path to a state file (overrides session)"
    ),
    session_id: str | None = Option(
        None, "--session-id", "-s", help="Session ID to use"
    ),
) -> str:
    """
    Configure a new simulation environment.

    This command creates a building with a specified number of floors and rooms,
    and optionally sets initial zombie infections. It can load from a config JSON file,
    and will either save the state to a file or to a new session folder.

    Parameters
    ----------
    floors_count : int, optional
        Number of floors to create in the building (default: DEFAULT_FLOORS).
    rooms_per_floor : int, optional
        Number of rooms per floor (default: DEFAULT_ROOMS_PER_FLOOR).
    infected : list of str, optional
        List of coordinates and zombie counts in the format 'floor,room:count'.
    config_file : str, optional
        Path to a configuration file containing floors, rooms, and infection data.
    state_file : str, optional
        If provided, the simulation state will be saved to this file instead of a session folder.
    session_id : str, optional
        The session ID to use; if not provided, a new one will be generated.

    Returns
    -------
    str
        The session ID used to save the simulation state.
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

    building = Building.from_2d_floor_spec(
        floors_count=floors_count, rooms_per_floor=rooms_per_floor
    )

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
                raise ValueError(
                    f"Invalid format '{item}'. Expected 'floor,room:count'."
                ) from e
        return infected_coords

    initial_infected = parse_infected(infected) if infected else {}
    initial_state = ZombieSimulationState(
        building=building,
        infected_coords=initial_infected,
        last_action="initialization",
        last_action_payload={"infected": initial_infected},
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
    step_action: int = Option(
        DO_NOTHING, help="Step-level action code (default is DO_NOTHING)"
    ),
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(
        None,
        "--state-file",
        help="Path to state file",
        resolve_path=True,
        writable=True,
    ),
):
    """
    Advance the simulation by one turn.

    Loads the simulation state, applies zombie spreading logic, and saves
    the updated state. An optional step-level action can be applied.

    Parameters
    ----------
    step_action : int, optional
        An optional numeric action code to apply during the step (default: DO_NOTHING).
    session_id : str, optional
        Session ID to load the state from.
    state_file : str, optional
        Path to the state file. If provided, it overrides session_id.

    Returns
    -------
    None
        The updated state is saved, and the new turn number is printed.
    """

    state = load_state(session_id, state_file)
    env = ZombieEnvironment(state)
    env.state = env.step(step_action)
    save_state(session_id, state_file, env.state)
    echo(f"Turn advanced to {env.state.turn}. Last action: {env.state.last_action}")


def fallback_config(
    ctx: Context,
    floors_count: int | None,
    rooms_per_floor: int | None,
    infected: list[str],
    state_file: str | None,
    session_id: str | None,
):
    """
    Fallback logic to reconfigure the simulation if any configuration options are provided.

    If floors, rooms, or infected coordinates are specified, it triggers the `configure` function.
    Used internally by composite commands like `run`.

    Parameters
    ----------
    ctx : Context
        Typer CLI context.
    floors_count : int, optional
        Number of floors to use for reconfiguration.
    rooms_per_floor : int, optional
        Number of rooms per floor for reconfiguration.
    infected : list of str
        List of coordinates and zombie counts in the format 'floor,room:count'.
    state_file : str, optional
        Path to a file to save the updated simulation state.
    session_id : str, optional
        Optional session ID to use.

    Returns
    -------
    str or None
        The session ID used after reconfiguration, or None if no reconfiguration was needed.
    """

    session_id = None
    # If any reconfiguration options are provided, call 'configure' and override.
    if floors_count is not None or rooms_per_floor is not None or infected:
        session_id = ctx.invoke(
            configure,
            floors_count=floors_count if floors_count is not None else DEFAULT_FLOORS,
            rooms_per_floor=rooms_per_floor
            if rooms_per_floor is not None
            else DEFAULT_ROOMS_PER_FLOOR,
            infected=infected,
            config_file=None,
            state_file=state_file,
            session_id=session_id,
        )
    return session_id


@simulation_app.command()
def run(
    ctx: Context,
    steps: int = Argument(10, help="Number of steps to run"),
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
    session_id: str | None = Option(None, "--session-id", "-s", help="Session ID"),
    state_file: str | None = Option(None, "--state-file", help="Path to state file"),
):
    """
    Run a composite simulation: optionally reconfigure, then simulate N steps.

    If any configuration options are passed (floors, rooms, infected), this will
    create a new building state before running the simulation. Then, it will run
    the specified number of turns.

    Parameters
    ----------
    ctx : Context
        Typer CLI context.
    steps : int
        Number of turns to simulate.
    floors_count : int, optional
        If set, reconfigures the simulation with this number of floors.
    rooms_per_floor : int, optional
        If set, reconfigures the simulation with this number of rooms per floor.
    infected : list of str, optional
        Coordinates to infect on setup, in the format 'floor,room:count'.
    session_id : str, optional
        The session ID to use. If none, a new one may be generated.
    state_file : str, optional
        Optional path to override default session-based state file.

    Returns
    -------
    None
        State is updated and saved after running the simulation.
    """

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
    for _ in range(steps):
        env.state = env.step()
    save_state(session_id, state_file, env.state)
    echo(
        f"Composite run complete. Turn: {env.state.turn}, Last action: {env.state.last_action}"
    )
