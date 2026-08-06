*This project has been created as part of the 42 curriculum by lmuler-f.*

# 🚁 Fly-in: Autonomous Fleet Routing System

## Description

**Fly-in** is an advanced Multi-Agent Pathfinding (MAPF) and simulation engine developed in Python 3.10+. The core objective is to route a fleet of $N$ autonomous drones from a starting hub (`start_hub`) to a target destination (`end_hub`) in the minimum possible number of simulation turns, adhering to strict graph topology and movement rules.

The system handles dynamic bottlenecks, capacity limits (`max_drones` per zone and `max_link_capacity` per connection), and varied movement costs:
- `normal`: Standard 1-turn cost.
- `priority`: 1-turn cost (preferred by pathfinding).
- `restricted`: 2-turn cost (drone occupies the connection during transit).
- `blocked`: Inaccessible zones.

---

## Algorithm Choices & Implementation Strategy

A naive shortest-path approach (such as static Dijkstra) fails in multi-agent environments because routing all drones along the same optimal path causes severe congestion, deadlocks, and capacity violations. 

To overcome this without using external graph libraries, Fly-in implements a **Space-Time Dijkstra Algorithm** paired with a **Reservation Table**:

1. **3D Search Space $(X, Y, Time)$:**
   - A node at turn $T$ is treated as a completely different state from the same node at turn $T+1$.
   - This allows drones to perform a **Wait Action** (staying at their current hub for 1 turn) to let other drones pass through narrow corridors.

2. **The Reservation Table:**
   - Acts as a global schedule. When Drone $i$ calculates its optimal path, it reserves the nodes and edges it will occupy at specific future turns.
   - Subsequent drones query this table. If a connection is at maximum capacity (`max_link_capacity`) at turn $T$, the algorithm automatically calculates a detour or schedules a strategic wait.

3. **Eager Movement & Tie-Breaking:**
   - To prevent "lazy movement" (where a drone waits unnecessarily because waiting early or late yields the same total turns), a microscopic cost penalty (`+1.001`) is applied to the Wait action. This forces drones to push forward eagerly, maximizing per-turn throughput.

4. **Performance Benchmark Achieved:**
   - The algorithm solves the quasi-unsolvable Challenger map (**"The Impossible Dream"**, 25 drones) in **39 turns**, crushing the reference record of 45 turns.

---

## Visual Representation & UX Features

Fly-in features a custom-built, high-performance graphical interface using **Pygame**, implementing the **MVC (Model-View-Controller)** pattern and a **Finite State Machine (FSM)**.

### 1. Viewport Camera & Fixed HUD
- **World Space vs. Screen Space:** The map is rendered in a 2D world coordinate system projected through a camera. Users can zoom (`Mouse Wheel`) and the camera remains anchored to the map's center.
- **Heads-Up Display (HUD):** A fixed UI layer anchored to the right side of the screen displays telemetry, turn counters, and control instructions, completely immune to camera zoom.

### 2. Semiotics & Functional Zone Shapes
Zones are visually differentiated by geometric shapes to allow instant tactical reading:
- **Circle:** `normal` zones.
- **Diamond / Losango:** `priority` zones (preferred routing).
- **Square:** `restricted` zones (2-turn transit delay).
- **Double-Ring Aura:** `start_hub` and `end_hub`.
- **Rainbow Effect:** Special dynamic color cycling for designated goal hubs.

### 3. Smooth LERP Animation & Time Travel
- **Linear Interpolation (LERP):** Drones smoothly glide along edges between turns instead of teleporting. Grid-offset interpolation prevents drones from visually overlapping when crowding a hub.
- **Time Travel (Rewind):** Because the simulation treats state as a pure function of time, users can hold the `[LEFT ARROW]` key to rewind the simulation turn-by-turn and inspect past routing decisions.

### 4. Interactive Menu & Dynamic Themes
- An interactive, keyboard-driven **Main Menu** (`STATE_MENU`) allows selecting maps by difficulty and switching visual themes on the fly:
  - **Sky:** Classic atmospheric flight.
  - **War:** Tactical radar/destroyed city with missile sprites.
  - **TrainStation:** Railway routing aesthetics.

---

## Instructions

### Prerequisites
- Python 3.10+
- `make`

### Makefile Rules

- `make install`: Creates a virtual environment (`.venv`) and installs required dependencies (`pygame`, `flake8`, `mypy`).
- `make run`: Launches the application in **Main Menu mode** (keyboard navigation).
- `make run MAP=<path_to_map>`: Bypasses the menu and launches directly into the simulation for a specific map (e.g., `make run MAP=maps/hard/03_ultimate_challenge.txt`).
- `make lint`: Validates the codebase using `flake8` and strict static type checking with `mypy --strict`.
- `make clean` / `make fclean`: Cleans temporary files, caches, and the virtual environment.

### Controls in Simulation
- `[SPACE]`: Toggle Auto-Play.
- `[RIGHT ARROW]`: Step forward 1 turn.
- `[LEFT ARROW]`: Rewind / Step backward 1 turn.
- `[M]`: Return to Main Menu.
- `[Q]` / `[ESC]`: Quit.

---

## Resources & AI Usage

### References
- *Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks* (MAPF literature).
- *Space-Time A\** and Cooperative Pathfinding algorithms.
- [Pygame Official Documentation](https://www.pygame.org/docs/).
- Python static typing (`typing` module / `mypy` PEP 484 & PEP 585).

### AI Usage Disclosure
In accordance with 42 curriculum guidelines, AI tools (LLMs) were used strictly as an interactive **Software Architecture Mentor** during the development of this project:
- **Algorithm Architecture:** AI was consulted to discuss the theoretical trade-offs between Flow-over-Time networks, Conflict-Based Search (CBS), and Space-Time Dijkstra/A\*, leading to the choice of the Reservation Table design.
- **Design Patterns:** Used to structure the Finite State Machine (FSM) for pygame scene transitions and the Model-View-Controller (MVC) separation between World projection and HUD rendering.
- **Debugging & Edge Cases:** Assisted in diagnosing UI debounce issues (`KEYUP` vs. `KEYDOWN` and UI Cooldown patterns) and refining strict type hints to achieve 100% `mypy --strict` compliance.
- **No Blind Copy-Pasting:** All core logic, graph building, parser rules, and Pygame rendering loops were understood, reviewed, tested, and implemented to adhere strictly to the project's rules and constraints.