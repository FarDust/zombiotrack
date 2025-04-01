from pydantic import BaseModel, Field

from zombiotrack.models.building import Building

InfectionState = dict[tuple[int, int], dict[str, str | int]]

class ZombieSimulationState(BaseModel):
    """
    Represents the current state of the zombie simulation, including
    the turn number, building configuration, and locations of zombies.

    Parameters
    ----------
    turn : int, optional
        The current turn in the simulation. Defaults to 0.
    building : List[List["Room"]]
        The structure of the building as a 2D grid of rooms.
    infected_coords : dict[tuple[int, int], dict[str, str]], optional
        The coordinates of all currently infected rooms. Each room is represented as a tuple of (x, y) coordinates. Defaults to an empty dictionary.
    events_log : List[str], optional
        A log of events for this state, such as movements or clean-ups. Defaults to an empty list.
    """

    turn: int = Field(0, ge=0, description="The current turn in the simulation.")
    "The current turn in the simulation."

    building: Building = Field(
        description="The structure of the building as a 2D grid of rooms."
    )
    "The structure of the building as a 2D grid of rooms."

    infected_coords: InfectionState = Field(
        default_factory=dict,
        description="The coordinates of all currently infected rooms and any additional information.",
    )
    "The coordinates of all currently infected rooms and any additional information."

    last_action: str = Field(
        default="START", description="The last action taken in the simulation."
    )
    "The last action taken in the simulation."

    last_action_payload: dict = Field(
        default_factory=dict, description="The payload associated with the last action."
    )

    infection_events_log: list[InfectionState] = Field(
        default_factory=list,
        description="A log of events for the infection state, such as infections or clean-ups on rooms.",
    )
    "A log of events for the infection state, such as infections or clean-ups on rooms."
