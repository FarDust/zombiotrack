from pydantic import BaseModel, Field
from typing import Literal

INITIAL_STATE = "normal"


class Sensor(BaseModel):
    """
    Represents an IoT sensor with a current status.

    Parameters
    ----------
    status : Literal['normal', 'alert']
        The current state of the sensor.
    """

    status: Literal["normal", "alert"] = Field(
        INITIAL_STATE,
        description="The current state of the sensor.",
    )
    "The current state of the sensor."

    def reset(self):
        """
        Reset the sensor status to normal.
        """
        self.status = INITIAL_STATE

    def trigger(self):
        """
        Trigger an alert on the sensor.
        """
        self.status = "alert"
