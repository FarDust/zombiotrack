from zombiotrack.models.building import Building
from zombiotrack.models.state import ZombieSimulationState
from zombiotrack.use_cases.constants import ZOMBIE_COUNT
from zombiotrack.use_cases.zombie_simulation import ZombieEnvironment


if __name__ == "__main__":
    # Initialize a new simulation state.
    initial_state = ZombieSimulationState(
        turn=0,
        building=Building.from_2d_floor_spec(floors_count=3, rooms_per_floor=4),
        infected_coords={(0, 0): {ZOMBIE_COUNT: 1}},
        events_log=[],
    )

    # Create a new simulation environment.
    env = ZombieEnvironment(initial_state, stochastic=True)

    # Run the simulation for 10 turns.
    for _ in range(10):
        env.state = env.step()

    # Print the final state of the simulation.
    print(env.state)
