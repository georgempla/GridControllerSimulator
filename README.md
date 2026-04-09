# Grid Controller Simulator

> *You are responsible for keeping the lights on for 100,000 people in the middle of Alaska. No pressure.*

Oakridge Grid Controller is a power systems simulation game built from scratch in Python and pygame. You play as the system operator of a fictional 1,500 MW nuclear based electrical grid in Oakridge, Alaska, managing generation dispatch, storage, interconnects, and load priorities in real time while the grid does its best to fall apart on you.


## What This Actually Is

The Oakridge grid is modelled with real electrical engineering principles, DC power flow via a B-matrix solver, the swing equation for frequency dynamics, ramp-rate-limited generation, seasonal demand profiles, stochastic forced outages, and weather driven renewable dispatch. The map is a graph of substations, generators, transmission lines, and load zones, each with their own physics and failure conditions.

The simulation runs in real time at 1x speed, but you can push it to 5x, 30x, or 60x to skip quiet periods. It slows back down automatically when something goes wrong (frequency falls below normal).

---

## The Oakridge Grid

The map covers a fictional Alaskan city with a diverse generation mix and several deliberate vulnerabilities:

**Generation**
- `GEN-001` Oakridge Nuclear Power Station, 1,500 MW pressurized water reactor. The anchor of the grid. Ramps at 2 MW/min. Takes 10 days to restart from cold. Do not trip it carelessly.
- `GEN-002` Chena River Hydroelectric Station, 420 MW run of river. Fast and flexible but derated heavily in winter when the river freezes.
- `GEN-003` Oakridge Combined Cycle Gas Plant, 480 MW. Your primary load-following tool. Ramps at 8 MW/min.
- `GEN-004` Ridgeline Wind Farm, 250 MW. Highly productive but intermittent. Can drop to zero in a storm.
- `GEN-005` South District Solar Array, 80 MW. Nearly useless in an Alaskan winter. Good in summer.
- `GEN-006/007` Gas Peaker Plants, 200 MW each. Fast (20 MW/min), expensive, high-emission. Start in standby. Only dispatch them when you need them.
- `GEN-008` Matanuska Biomass Station, 55 MW. Slow but steady. Provides regional north district supply.

**Storage**
- `STG-001` Grid Battery, 200 MWh lithium-ion. Responds in 0.2 seconds. Use it for frequency regulation and renewable smoothing.
- `STG-002` Chena Pumped Hydro, 1,200 MWh. Responds in 30 seconds. Bulk overnight storage. Charges on nuclear surplus, discharges during morning and evening peaks.

**Interconnects**
- `IC-001` HVDC link to the Southern Alaska grid. Up to 800 MW export, 600 MW import. Ramps at 50 MW/min. You are contractually obligated to export, failing to deliver costs you.

**Known vulnerabilities (by design)**
- `SUB-005` South Residential Substation has no N-1 redundancy. One transformer failure blacks out 27,000 households.
- `PIPE-001` is a single natural gas pipeline feeding all three gas generators. One rupture removes 880 MW simultaneously.
- `TL-011` Downtown-South 138 kV line is single-circuit and aging. A fault here isolates the southern suburbs.
- The wind collection line `TL-008` is single-circuit. Loss curtails all wind generation instantly.

---

## Frequency Governs Everything

The grid runs at 60 Hz. Frequency deviates when generation and load are not balanced, it falls when there is a deficit, rises when there is a surplus. The rate of change is governed by the inertia of every spinning turbine online at that moment. More spinning mass means slower frequency change means more time to respond.

| Frequency | Status | What happens                              |
|-----------|--------|-------------------------------------------|
| 60.0 Hz | Nominal | Nothing                                   |
| 59.5 Hz | Warning | You should already be dispatching         |
| 59.2 Hz | Alert | Dispatch now                              |
| 58.8 Hz | Emergency | You should probably be shedding some load |
| 58.4 Hz | Collapse | Game over                                 |

Your score accumulates based on how long you hold frequency near nominal and how much you are exporting. A perfect session at full export scores around 3,600 points per hour. Importing costs you.

---

## Controls

**Map navigation**
- Scroll wheel to zoom in/out, centred on cursor
- Left click and drag to pan

**Interacting with nodes**
- Left click any node opens the Info Panel for that facility
- Click elsewhere dismisses the Info Panel
- Multiple panels can be open simultaneously, z-ordered by click time

**Info Panel controls**
- Text field + Enter set a generator or storage setpoint in MW
- TRIP begins ramping a generator to zero
- RESTART returns a standby generator to minimum output (or starts its startup timer)
- SHED LOAD / RESTORE manually interrupt or restore interruptible industrial loads
- IDLE / MAX CHG / MAX DIS storage shortcuts

**HUD**
- Frequency gauge (top centre) your primary instrument
- Gen vs Load bar (bottom centre) real-time balance, green is surplus, red is deficit
- Status panel (top left) time, season, score, speed controls
- Alarms panel (top right) active alarms and HVDC flow, CLEAR to dismiss
- Score breakdown (appears when hovering over score) details on your score

**Settings**
- Option to fullscreen the game
- Adjustable grid frequency between 50hz and 60hz
- Ability to adjust your music volume from 0 to 100
- Option to prevent fast-paced music from playing
---

## Scoring

Your score accumulates every second based on two factors:

- **Frequency** 50% weight. Full points within ±0.1 Hz of nominal, reduced points in the warning band, zero points in emergency, no accumulation during collapse.
- **HVDC export** 30% weight. Full export earns full points. Import reduces your score. You can go negative.
- **Battery usage** 20% weight. Full charging earns full points. Discharging reduces your score. You can go negative.

There is no time limit. Your final score is shown on the game over screen when the grid collapses.

---

## Getting Started

**Requirements**
```
Python 3.10+
pygame
numpy
```

**Install dependencies**
```bash
pip install pygame numpy
```

**Run**
```bash
python main.py
```

**Build a standalone executable**
```bash
pip install pyinstaller pillow
python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico',format='ICO',sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])"
pyinstaller --onefile --windowed --icon="assets/grid_controller.ico" --add-data "maps;maps" --add-data "utils;utils" --add-data "assets;assets" --name "GridControllerSimulator" main.py
```
The exe will be in `dist/`.

Or just download the release exe

---

## Project Structure

```
GridControllerSimulator/
├── main.py                   
├── maps/
│   └── oakridge_grid.json
├── utils/
│   ├── camera.py
│   ├── icons.py
│   ├── hud.py
│   ├── infopanels.py
│   ├── map_renderer.py
│   ├── simulationEngine.py
│   ├── game_over.py
│   ├── main_menu.py
│   ├── settings.py
│   ├── tutorial.py
│   └── disclaimer.py
└── assets/
    ├── grid_controller.ico
    ├── grid_controller.png
    ├── alert.ogg
    ├── ambient1.ogg
    ├── ambient2.ogg
    └── ambient3.ogg
```

The grid is fully data-driven. Every generator, substation, line, load, and event is defined in `oakridge_grid.json`. The simulation code does not hardcode any grid-specific values, adding a new generator or substation means editing the JSON, not the engine.

---

## What's Coming

These are planned but not yet built. They're grayed out in the menu for a reason.

- **Sandbox Mode** no failure conditions, unlimited dispatch, good for learning the map
- **Campaign Mode** structured missions with specific objectives and escalating scenarios  
- **Custom Scenarios** scripted crisis events: nuclear trip, gas pipeline rupture, arctic storm, cyberattack on SCADA
- **Custom Map Support** load your own grid JSON and play on it
- **Achievements** track records across sessions, unlock bonus scenarios
- **Energy Market** spot pricing, long-term contracts, trading decisions, revenue management

---

## A Note on the Physics

The simulation uses a DC power flow model (B-matrix, solved with numpy's linear algebra solver each tick) for line flows, and the swing equation for frequency dynamics. These are standard simplifications used in power systems education and operator training software, they're not full AC power flow, they ignore reactive power and voltage magnitude, and the inertia constants are ballpark values.

---

## Bug fixes
- Line overload timers accumulate incorrectly under some conditions, cascade behaviour may be more aggressive than intended
- Incorrect error handling leading to silent failures when calculating b_matrix
- Fixed load on all lines defaulting to 0
- Fixed isolated nodes continuing to receive or provide power

## Known Issues (Alpha)

- Forced outages on some generators may not correctly transition to standby without manual intervention
- The solar output model uses integer hours internally, a fix for smooth continuous output is pending
- Performance degrades slightly at very high zoom with many open info panels
- No save/load system yet, each session starts fresh

