# 🧟 Zombiotrack

A console-based zombie simulation system powered by IoT sensors and panic.

Zombiotrack models a building infested with zombies. Each room has a sensor that can detect the presence of undeads. The simulation allows users to configure, control, and visualize the infection across multiple floors using a CLI interface powered by [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/) for visuals, and [Pydantic v2](https://docs.pydantic.dev/latest/) for strict modeling.

> Minimalistic. Extendable. Fun to blow up. 💥

---

## ⚙️ Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager & build system)

---

## 🚀 Installation

Clone this repo and install dependencies using `uv`:

```bash
uv sync
```

You can add packages via:

```bash
uv add <package-name>
```

---

## ▶️ How to Run

### 💡 Start with CLI entrypoint:

```bash
zombiotrack-cli --help
```

This will show all available subcommands.

---

## 🧠 Basic Usage

### 🔧 Configure a simulation

```bash
zombiotrack-cli simulation configure --floors-count 3 --rooms-per-floor 4 --infected "0,0:2" --infected "1,2:5"
```

- You’ll get a `session_id` printed.
- Simulation state is saved in `sessions/<session-id>/zombie-simulation-state.json`.

You can also load from a config file:

```bash
zombiotrack-cli simulation configure --config-file config.json
```

### 🔁 Step the simulation forward

```bash
zombiotrack-cli simulation step --session-id <your-session-id>
```

---

## 💥 Interactive Mode

You can use a live terminal menu to interact with your simulation:

```bash
zombiotrack-cli menu run
```

This mode allows you to:

- Advance turns
- Clean or block rooms
- Reset sensors
- Visualize the infection grid
- Reset the whole simulation (💥 nuking option)

If no session or config is passed, you'll be prompted for values.

---

## 🧱 Grid Visualization

```bash
zombiotrack-cli view grid --session-id <your-session-id>
```

The grid shows:

- 🟩 **Green**: normal sensor  
- 🟥 **Red**: alert sensor  
- 🔵 **Blue**: blocked room  
- Zombie count shown inside the cell (e.g. `3`, `[2]` if blocked)

---

## 🔎 Show Raw Simulation State

```bash
zombiotrack-cli view show-state --session-id <your-session-id>
```

You can inspect a specific JSON path using `--json-path`, for example:

```bash
zombiotrack-cli view show-state --session-id <your-session-id> --json-path "$.building.floors.3.rooms.3"
```

---

## 📁 Project Structure

```
zombiotrack/
├── interfaces/
│   └── cli/              # Typer CLI interface: commands, constants, API routing
│
├── models/               # Pydantic models: Building, Floor, Room, Sensor, State
│
├── use_cases/            # Core simulation logic and constants
│   └── zombie_simulation.py  # ZombieEnvironment and infection logic
│
├── infrastructure/       # (Empty for now) Reserved for future persistence or DB logic
│
├── __main__.py           # Optional CLI bootstrap entry
```

---

## 📦 Packaging

This project uses `uv` as build backend and installer.  
To install the CLI tool locally:

```bash
uv sync
```

---

## 🧊 Example Snippet

```python
from zombiotrack.models.state import ZombieSimulationState
from zombiotrack.simulation.env import ZombieEnvironment

state = ZombieSimulationState(...)  # build your state
env = ZombieEnvironment(state)

for _ in range(10):
    env.step()

print(env.state)
```
---

## 🧠 Design & Architectural Assumptions

The following assumptions guided the system's **design decisions**, **simulation logic**, and **overall architecture**:

### 🧱 Simulation Design

- **Zombies are not entities**  
  Zombies are not modeled as objects. Instead, each infected room is tracked using a `zombie_count` stored in the `infected_coords` dictionary of the simulation state.

- **Sensors are triggered on entry only**  
  - When zombies enter a room, its sensor switches to `alert`.  
  - Once triggered, the sensor **remains in `alert`**, even if the room becomes empty.  
  - The user must explicitly reset a sensor if needed.

- **Zombie movement is a transfer**  
  Infection logic always **removes all zombies** from the origin room and redistributes them to adjacent rooms. No zombies remain behind after spreading.

- **Blocked rooms are infection-proof**  
  If a room is marked as blocked, it:
  - Cannot receive infection.
  - Does not spread infection.
  - Acts as a hard wall during propagation.

- **Each turn is a single atomic step**  
  A call to `env.step()` performs one full propagation step, increments the turn counter, and updates sensor states. Actions within `step()` are isolated from direct CLI actions.

- **Actions are explicitly categorized**  
  - `step()` handles **turn-level actions** like `do_nothing` or future modifiers.  
  - The environment also exposes **direct mutation commands** like `clean_room`, `reset_simulation`, `block_room`, etc., which operate outside the step cycle.

---

### 🏗️ Architecture and Extensibility

- **CLI is isolated from simulation logic**  
  - The CLI layer (powered by `Typer`) only handles argument parsing, session loading/saving, and output visualization.
  - All business logic is encapsulated in the `ZombieEnvironment` and `ZombieSimulationState` classes.

- **Session-based persistence is simple and portable**  
  - All simulation state is stored in JSON files under `sessions/<session-id>/zombie-simulation-state.json`.
  - This makes the system portable, transparent, and easy to inspect or manipulate.

- **Typed and validated Pydantic models**  
  - The simulation state uses Pydantic v2, ensuring robust validation.
  - Dictionary keys like `(floor, room)` are deserialized from JSON string keys via `model_validator`.

- **Visual output is decoupled and terminal-friendly**  
  - Grid visualization uses `rich.Table`, with coloring based on sensor state and zombie count intensity.
  - Design is CLI-first but supports future UI replacement.

- **API-ready by design**  
  The architecture was consciously built to support future extensions, such as:
  - A web API (e.g., FastAPI) to manipulate sessions and control simulations via HTTP.
  - Switching to a document-based NoSQL database (e.g., MongoDB) for state persistence.
  - Using session IDs as query parameters or path variables in REST endpoints.

  Since the CLI only handles input/output and all logic is in `ZombieEnvironment`, porting to an API would require minimal effort. The only difference would be replacing file persistence with database operations.

---

## 🧔 Author

Made with brains, discipline, and a bit of chaos  
by *Gabriel Faundez* 🧠🔥  
https://fardust.tralmor.com/experience

---

## 🧟‍♂️ License

Unlicensed. Zombies don't care about intellectual property.
