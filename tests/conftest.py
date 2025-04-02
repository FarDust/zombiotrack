import pytest
from zombiotrack.models.building import Building
from zombiotrack.models.state import ZombieSimulationState
from zombiotrack.use_cases.zombie_simulation import ZombieEnvironment


@pytest.fixture
def base_building():
    def _create(floors=1, rooms=1):
        return Building.from_2d_floor_spec(floors_count=floors, rooms_per_floor=rooms)

    return _create


@pytest.fixture
def base_state(base_building):
    def _create(floors, rooms, infected=None):
        building = base_building(floors, rooms)
        return ZombieSimulationState(building=building, infected_coords=infected or {})

    return _create


@pytest.fixture
def zombie_env(base_state):
    def _create(floors=1, rooms=1, infected=None):
        state = base_state(floors, rooms, infected)
        return ZombieEnvironment(state)

    return _create
