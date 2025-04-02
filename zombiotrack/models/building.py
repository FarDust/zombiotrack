from pydantic import BaseModel, Field, model_validator

from zombiotrack.models.floor import Floor
from zombiotrack.models.room import Room
from zombiotrack.models.sensor import Sensor


class Building(BaseModel):
    """
    Represents a building equipped with IoT sensors for zombie simulation.

    Parameters
    ----------
    floors_count : int
        Total number of floors in the building. Must be greater than 0.
    rooms_per_floor : int
        Number of rooms per floor. Must be greater than 0.
    floors : list, optional
        A list to hold floor objects. Can be initialized empty.
    """

    floors_count: int = Field(
        1,
        gt=0,
        description="Total number of floors in the building.",
    )
    "Total number of floors in the building."

    rooms_per_floor: int = Field(
        1,
        gt=0,
        description="Number of rooms per floor.",
    )
    "Number of rooms per floor."

    floors: dict[int, Floor] = Field(
        default_factory=list,
        description="List of Floor objects in the building.",
    )
    "List of Floor objects in the building."

    @model_validator(mode="after")
    def validate_floors(self) -> "Building":
        if len(self.floors) > self.floors_count:
            raise ValueError(
                f"Too many floor definitions: got {len(self.floors)}, expected at most {self.floors_count}."
            )

        return self

    @classmethod
    def from_2d_floor_spec(
        cls,
        floors_count: int,
        rooms_per_floor: int,
    ) -> "Building":
        """
        Create a Building object from a floor specification.

        Parameters
        ----------
        floors_count : int
            Total number of floors in the building.
        rooms_per_floor : int
            Number of rooms per floor.
        Returns
        -------
        Building
            A Building object with the specified floors and rooms.
        """
        floors: dict[int, Floor] = {}

        for floor_number in range(floors_count):
            floor = Floor(floor_number=floor_number)
            for room_number in range(rooms_per_floor):
                new_room = Room(
                    room_number=room_number,
                    sensor=Sensor(),
                )
                floor.rooms[room_number] = new_room
            floors[floor_number] = floor

        return cls(
            floors_count=floors_count,
            rooms_per_floor=rooms_per_floor,
            floors=floors,
        )

    def update_building_size(
        self,
        new_floors_count: int,
        new_rooms_per_floor: int,
    ):
        """
        Update the building size by adding or removing floors and rooms.

        Parameters
        ----------
        new_floors_count : int
            New total number of floors in the building.
        new_rooms_per_floor : int
            New number of rooms per floor.
        """
        if new_floors_count < self.floors_count:
            self.floors = {k: v for k, v in self.floors.items() if k < new_floors_count}
        elif new_floors_count > self.floors_count:
            for floor_number in range(self.floors_count, new_floors_count):
                floor = Floor(floor_number=floor_number)
                for room_number in range(new_rooms_per_floor):
                    new_room = Room(
                        room_number=room_number,
                        sensor=Sensor(),
                    )
                    floor.rooms[room_number] = new_room
                self.floors[floor_number] = floor

        if new_rooms_per_floor != self.rooms_per_floor:
            for floor in self.floors.values():
                if new_rooms_per_floor < self.rooms_per_floor:
                    floor.rooms = {
                        k: v for k, v in floor.rooms.items() if k < new_rooms_per_floor
                    }
                elif new_rooms_per_floor > self.rooms_per_floor:
                    for room_number in range(self.rooms_per_floor, new_rooms_per_floor):
                        new_room = Room(
                            room_number=room_number,
                            sensor=Sensor(),
                        )
                        floor.rooms[room_number] = new_room

        self.floors_count = new_floors_count
        self.rooms_per_floor = new_rooms_per_floor
