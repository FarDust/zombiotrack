from pydantic import BaseModel, Field

from zombiotrack.models.room import Room


class Floor(BaseModel):
    """
    Represents a floor within the building, containing multiple rooms.

    Parameters
    ----------
    floor_number : int
        The floor index (e.g., 0 for ground floor).
    rooms : list, optional
        A list to hold Room objects. Initialized as empty by default.
    """

    floor_number: int = Field(
        0,
        ge=0,
        description="The floor index (e.g., 0 for ground floor).",
    )
    "The floor index (e.g., 0 for ground floor)."

    rooms: dict[int, Room] = Field(
        default_factory=dict,
        description="List of Room objects on this floor.",
    )
    "List of Room objects on this floor."
