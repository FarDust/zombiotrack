from pydantic import BaseModel, Field

from zombiotrack.models.sensor import Sensor


class Room(BaseModel):
    """
    Represents a room in the building monitored by an IoT sensor.

    Parameters
    ----------
    room_number : int
        The identifier for the room within its floor.
    sensor : Sensor
        The IoT sensor installed in the room.
    """

    room_number: int = Field(
        0,
        ge=0,
        description="The identifier for the room within its floor.",
    )
    "The identifier for the room within its floor."

    blocked: bool = Field(
        False,
        description="Whether the room is blocked.",
    )

    sensor: Sensor = Field(
        description="The IoT sensor installed in the room.",
    )
    "The IoT sensor installed in the room."
