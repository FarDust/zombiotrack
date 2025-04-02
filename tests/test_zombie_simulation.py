from zombiotrack.models.building import Building
from zombiotrack.models.state import ZombieSimulationState
from zombiotrack.use_cases.constants import ZOMBIE_COUNT
from zombiotrack.use_cases.zombie_simulation import ZombieEnvironment


def test_initial_infection_triggers_sensor():
    building = Building.from_2d_floor_spec(1, 2)
    infected = {(0, 0): {ZOMBIE_COUNT: 1}}
    state = ZombieSimulationState(building=building, infected_coords=infected)
    env = ZombieEnvironment(state)

    assert env.state.building.floors[0].rooms[0].sensor.status == "alert"
    assert env.state.building.floors[0].rooms[1].sensor.status == "normal"


def test_step_advances_turn():
    building = Building.from_2d_floor_spec(1, 1)
    infected = {(0, 0): {ZOMBIE_COUNT: 1}}
    state = ZombieSimulationState(building=building, infected_coords=infected)
    env = ZombieEnvironment(state)

    old_turn = env.state.turn
    env.state = env.step()
    assert env.state.turn == old_turn + 1


def test_clean_room_removes_infection():
    building = Building.from_2d_floor_spec(1, 1)
    infected = {(0, 0): {ZOMBIE_COUNT: 2}}
    state = ZombieSimulationState(building=building, infected_coords=infected)
    env = ZombieEnvironment(state)

    env.clean_room(0, 0)
    assert (0, 0) not in env.state.infected_coords


def test_reset_sensor():
    building = Building.from_2d_floor_spec(1, 1)
    infected = {(0, 0): {ZOMBIE_COUNT: 1}}
    state = ZombieSimulationState(building=building, infected_coords=infected)
    env = ZombieEnvironment(state)

    env.reset_sensor(0, 0)
    assert env.state.building.floors[0].rooms[0].sensor.status == "normal"


def test_sensor_alert_on_startup(zombie_env):
    env = zombie_env(1, 1, {(0, 0): {ZOMBIE_COUNT: 1}})
    assert env.state.building.floors[0].rooms[0].sensor.status == "alert"


def test_zombie_spread_adjacent_rooms(zombie_env):
    env = zombie_env(1, 3, {(0, 1): {ZOMBIE_COUNT: 3}})
    next_state = env.step()
    infected = next_state.infected_coords
    assert (0, 0) in infected or (0, 2) in infected


def test_zombie_cross_floor_infection(zombie_env):
    env = zombie_env(2, 1, {(0, 0): {ZOMBIE_COUNT: 2}})
    next_state = env.step()
    assert (1, 0) in next_state.infected_coords


def test_blocked_room_prevents_infection(zombie_env):
    env = zombie_env(1, 2, {(0, 0): {ZOMBIE_COUNT: 2}})
    env.state.building.floors[0].rooms[1].blocked = True
    next_state = env.step()
    assert (0, 1) not in next_state.infected_coords


def test_clean_room_removes_zombies(zombie_env):
    env = zombie_env(1, 1, {(0, 0): {ZOMBIE_COUNT: 2}})
    env.clean_room(0, 0)
    assert (0, 0) not in env.state.infected_coords


def test_sensor_reset_sets_status_to_normal(zombie_env):
    env = zombie_env(1, 1, {(0, 0): {ZOMBIE_COUNT: 1}})
    env.reset_sensor(0, 0)
    assert env.state.building.floors[0].rooms[0].sensor.status == "normal"


def test_block_unblock_room(zombie_env):
    env = zombie_env(1, 1)
    env.block_room(0, 0)
    assert env.state.building.floors[0].rooms[0].blocked
    env.unblock_room(0, 0)
    assert not env.state.building.floors[0].rooms[0].blocked


def test_reset_simulation_keeps_structure(zombie_env):
    env = zombie_env(1, 1, {(0, 0): {ZOMBIE_COUNT: 1}})
    env.reset_simulation(infected_coords=None)
    assert env.state.turn == 0
    assert env.state.infected_coords == {}
    assert len(env.state.building.floors) == 1
