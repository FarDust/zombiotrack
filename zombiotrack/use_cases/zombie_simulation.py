from copy import deepcopy
from random import random, randint
from zombiotrack.models.building import Building
from zombiotrack.models.floor import Floor
from zombiotrack.models.state import InfectionState, ZombieSimulationState
from zombiotrack.use_cases.constants import (
    DO_NOTHING,
    INFECTION_PROBABILITY,
    ZOMBIE_COUNT,
    ZOMBIE_COUNT_DELTA,
)


class ZombieEnvironment:
    """
    A simulation environment for a zombie invasion.

    This class provides operations to update the simulation state.
    The `step` method advances the simulation by one turn (propagating zombies)
    and can apply an additional step-level action defined via a lookup table.
    Other public methods (clean_room, reset_sensor, block_room, unblock_room, reset_simulation,
    god_mode) modify the environment directly via CLI commands.

    The environment stores its current state in `self.state`, and every method returns
    a new, updated state.
    """

    def __init__(self, initial_state: ZombieSimulationState,  stochastic: bool = False):
        # Store the current state of the simulation.
        self.state = deepcopy(initial_state)
        # Lookup table: number -> action name, default action (0) is "do_nothing"
        self.step_action_lookup = {
            DO_NOTHING: "do_nothing",  # Default action
            # Future step-level actions can agregate more mappings.
        }

        self.stochastic: bool = stochastic

    def _apply_update(
        self,
        state: ZombieSimulationState,
        old_state: ZombieSimulationState,
        action: str,
        payload: dict,
    ) -> ZombieSimulationState:
        """
        Helper to update the state's last_action and log the new state snapshot.

        Parameters
        ----------
        state : ZombieSimulationState
            The simulation state to update.
        action : str
            A description of the action applied.

        Returns
        -------
        ZombieSimulationState
            The updated simulation state.
        """
        state.last_action = action
        state.last_action_payload = payload
        self.state = deepcopy(state)
        return state

    def step(self, action: int = 0) -> ZombieSimulationState:
        """
        Advances the simulation by one turn, propagating zombie infection,
        and applies an additional step-level action from the lookup table.

        The simulation state is stored internally (self.state) and updated in-place.

        Parameters
        ----------
        step_action : int, optional
            The number representing a step-level action to apply (default is 0, "do_nothing").

        Returns
        -------
        ZombieSimulationState
            The new simulation state after advancing one turn.
        """

        new_state = deepcopy(self.state)
        new_state.turn += 1

        # Apply the default action if the action number is not in the lookup table.
        if action != 0 and action not in self.step_action_lookup:
            action_name = self.step_action_lookup.get(action, "do_nothing")
            new_state = getattr(self, action_name)(new_state)

        # Apply the infection spread.
        new_state = self._spread_infection(new_state)

        return new_state

    def _room_is_blocked(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> bool:
        """
        Checks if a room is blocked.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        bool
            True if the room is blocked, False otherwise.
        """
        return state.building.floors[floor].rooms[room].blocked

    def _assert_bounds(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> None:
        """
        Ensure if the given floor and room numbers are within the building bounds.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the floor or room numbers are out of bounds.
        """
        if floor < 0 or floor >= len(state.building.floors):
            raise ValueError("Invalid starting floor number.")
        if room < 0 or room >= len(state.building.floors[floor].rooms):
            raise ValueError("Invalid starting room number.")

    def _check_room_exists(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> bool:
        """
        Check if a room exists in the building.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        bool
            True if the room exists, False otherwise.
        """
        floor: Floor | None = state.building.floors.get(floor)
        if floor is None:
            return False
        return room in floor.rooms

    def _check_bounds(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> bool:
        """
        Check if the given floor and room numbers are within the building bounds.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        bool
            True if the floor and room numbers are within bounds, False otherwise.
        """
        return 0 <= floor < len(state.building.floors) and 0 <= room < len(
            state.building.floors[floor].rooms
        )

    def _check_infected(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> bool:
        """
        Check if a room is infected.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        bool
            True if the room is infected, False otherwise.
        """
        if state.infected_coords[(floor, room)].get(ZOMBIE_COUNT, 0) == 0:
            return False
        return True

    def _spread_infection(self, state: ZombieSimulationState) -> ZombieSimulationState:
        """
        Spreads the infection to adjacent rooms.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after spreading the infection.
        """
        new_state = deepcopy(state)
        infection_actions: list[InfectionState] = []
        for floor, room in state.infected_coords:
            if self._check_infected(new_state, floor, room):
                room_infection_actions = self._spread_infection_room(new_state, floor, room)
                infection_actions.extend(room_infection_actions)
        for infection_action in infection_actions:
            new_state = self._apply_infection_action(new_state, infection_action)
        new_state.infection_events_log += infection_actions
        new_state = self._apply_update(
            state=new_state,
            old_state=state,
            action="spread_infection",
            payload={
                "stochastic": self.stochastic,
            },
        )
        return new_state
    
    def _apply_infection_action(
        self, state: ZombieSimulationState, infection_action: InfectionState
    ) -> ZombieSimulationState:
        """
        Applies an infection action to the current state. Also sends messages to
        teh required devices if is required.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        infection_action : InfectionState
            The infection action to apply.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after applying the infection action.
        """
        for room, attributes in infection_action.items():
            if room not in state.infected_coords:
                state.infected_coords[room] = {}
            for attribute, value in attributes.items():
                if attribute == ZOMBIE_COUNT_DELTA:
                    if value > 0:
                        state.building.floors[room[0]].rooms[room[1]].sensor.trigger()
                    if ZOMBIE_COUNT not in state.infected_coords[room]:
                        state.infected_coords[room][ZOMBIE_COUNT] = 0
                    state.infected_coords[room][ZOMBIE_COUNT] = max(0, state.infected_coords[room].get(ZOMBIE_COUNT, 0) + value)
        return state

    def _spread_infection_room(
        self, state: ZombieSimulationState, floor: int, room: int
    ) -> list[InfectionState]:
        """
        Spreads the infection to an adjacent room.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        list[InfectionState]
            A list of InfectionState that would represent the actions taken over the `infected_coords` attribute.
        """

        assert self._check_bounds(state, floor, room), "Invalid room coordinates."
        assert self._check_room_exists(state, floor, room), "Room does not exist."
        assert not self._room_is_blocked(state, floor, room), "Room is blocked."

        # Check if the room is infected and has zombies.
        if not self._check_infected(state, floor, room):
            return state

        # Get the list of adjacent rooms.
        possible_adjacent_rooms: set[tuple[int, int]] = set()

        for i in range(-1, 2):
            for j in range(-1, 2):
                if abs(i) + abs(j) != 1:
                    continue
                if (
                    self._check_bounds(state, floor + i, room + j)
                    and not self._room_is_blocked(state, floor + i, room + j)
                    and self._check_room_exists(state, floor + i, room + j)
                ):
                    possible_adjacent_rooms.add((floor + i, room + j))

        infection_place_state = state.infected_coords.get((floor, room), {})

        infection_power: int = infection_place_state.get(ZOMBIE_COUNT, 1)

        infection_status: int = 0

        infection_actions: list[InfectionState] = []

        # Spread the infection to a random adjacent room.
        for adjacent_room in possible_adjacent_rooms:
            if self.stochastic:
                if random() < INFECTION_PROBABILITY:
                    strength = randint(0, infection_power)
                    infection_action = self._infect_room(
                        state,
                        adjacent_room[0],
                        adjacent_room[1],
                        quantity=strength,
                    )
                else:
                    continue
            else:
                strength = max(infection_power // max(len(possible_adjacent_rooms), 1), 1)
                infection_action = self._infect_room(
                    state,
                    adjacent_room[0],
                    adjacent_room[1],
                    quantity=strength,
                )
            infection_status += strength
            infection_actions.append(infection_action)

        # Remove extra zombies from the current room.
        infection_actions.append({(floor, room): {
            ZOMBIE_COUNT_DELTA: min(0, infection_power - infection_status),
        }})

        
        return infection_actions

    def _infect_room(
        self, state: ZombieSimulationState, floor: int, room: int, quantity: int
    ) -> ZombieSimulationState:
        """
        Infects a room with zombies.

        Parameters
        ----------
        state : ZombieSimulationState
            The current simulation state.
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        InfectionState
            An instance of the InfectionState that would represent an action over the `infected_coords` attribute.
        """

        assert self._check_bounds(state, floor, room), "Invalid room coordinates."
        assert self._check_room_exists(state, floor, room), "Room does not exist."
        assert not self._room_is_blocked(state, floor, room), "Room is blocked."
        return {
            (floor, room): {
                ZOMBIE_COUNT_DELTA: quantity,
            }
        }

    def clean_room(self, floor: int, room: int) -> ZombieSimulationState:
        """
        Cleans a room by removing its infection.

        Parameters
        ----------
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after cleaning the room.
        """
        new_state = deepcopy(self.state)
        self._assert_bounds(new_state, floor, room)
        new_state.infected_coords.popitem((floor, room))
        new_state = self._apply_update(
            new_state,
            "clean_room",
            {
                "floor": floor,
                "room": room,
            },
        )
        self.state = deepcopy(new_state)
        return new_state

    def reset_sensor(self, floor: int, room: int) -> ZombieSimulationState:
        """
        Resets the sensor for a specified room.

        Parameters
        ----------
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after resetting the sensor.
        """
        new_state = deepcopy(self.state)
        self._assert_bounds(new_state, floor, room)
        self.state.building.floors[floor].rooms[room].sensor.reset()
        new_state = self._apply_update(
            new_state,
            "reset_sensor",
            {
                "floor": floor,
                "room": room,
            },
        )
        self.state = deepcopy(new_state)
        return new_state

    def block_room(self, floor: int, room: int) -> ZombieSimulationState:
        """
        Blocks a room to prevent zombie infection.

        Parameters
        ----------
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after blocking the room.
        """
        new_state = deepcopy(self.state)
        self._assert_bounds(new_state, floor, room)
        new_state.building.floors[floor].rooms[room].blocked = True
        new_state = self._apply_update(
            new_state,
            "block_room",
            {
                "floor": floor,
                "room": room,
            },
        )
        self.state = deepcopy(new_state)
        return new_state

    def unblock_room(self, floor: int, room: int) -> ZombieSimulationState:
        """
        Unblocks a previously blocked room.

        Parameters
        ----------
        floor : int
            The floor number.
        room : int
            The room number.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after unblocking the room.
        """
        new_state = deepcopy(self.state)
        self._assert_bounds(new_state, floor, room)
        new_state.building.floors[floor].rooms[room].blocked = False
        new_state = self._apply_update(new_state, "unblock_room", {})
        self.state = deepcopy(new_state)
        return new_state

    def reset_simulation(self) -> ZombieSimulationState:
        """
        Resets the simulation, clearing infections and setting the turn to zero.

        Returns
        -------
        ZombieSimulationState
            The new simulation state after a full reset.
        """
        new_state = ZombieSimulationState(
            turn=0,
            building=Building.from_2d_floor_spec(
                floors_count=self.state.building.floors_count,
                rooms_per_floor=self.state.building.rooms_per_floor,
            ),
            infected_coords={},
            events_log=[],
        )
        new_state = self._apply_update(new_state, "reset_simulation")
        self.state = deepcopy(new_state)
        return new_state
