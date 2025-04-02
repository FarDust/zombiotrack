import json
from pathlib import Path

from typer import Exit, echo

from zombiotrack.interfaces.cli.config import SESSIONS_DIR
from zombiotrack.models.state import ZombieSimulationState


def get_state_filepath(session_id: str | None, state_file: str | None) -> Path:
    """
    Returns the file path to the state file.
    If state_file is provided, returns its Path.
    Otherwise, returns sessions/<session_id>/zombie-simulation-state.json.
    """
    if state_file:
        return Path(state_file).absolute().resolve()
    session_folder = SESSIONS_DIR / session_id
    session_folder.mkdir(exist_ok=True)
    return session_folder / "zombie-simulation-state.json"


def load_state(session_id: str | None, state_file: str | None) -> ZombieSimulationState:
    """
    Loads the simulation state from a file. If session_id is provided,
    the state file is assumed to be in sessions/<session_id>/zombie-simulation-state.json.
    """
    if not session_id and not state_file:
        echo("You must provide either a session ID or a state file path.")
        raise Exit()
    filepath = get_state_filepath(session_id, state_file)
    if not filepath.exists():
        echo(f"State file '{filepath}' does not exist. Please run 'configure' first.")
        raise Exit()

    return ZombieSimulationState(**json.loads(filepath.read_text()), strict=True)


def save_state(
    session_id: str | None, state_file: str | None, state: ZombieSimulationState
) -> None:
    """
    Saves the simulation state to the appropriate file.
    """
    filepath = get_state_filepath(session_id, state_file)
    filepath.write_text(state.model_dump_json(indent=2, warnings="error"))
