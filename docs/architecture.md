# Architecture Guide

> **Cargo Optimization Web App** — Written for data scientists who know optimization
> but may be new to software engineering patterns. Every term is defined before it is used.

---

## Table of Contents

1. [What is "Software Architecture"?](#1-what-is-software-architecture)
2. [What is a "Service"?](#2-what-is-a-service)
3. [The Big Picture: Four Layers](#3-the-big-picture-four-layers)
4. [Layer 1 — Domain](#4-layer-1--domain)
5. [Layer 2 — Application](#5-layer-2--application)
6. [Layer 3 — Infrastructure](#6-layer-3--infrastructure)
7. [Layer 4 — Controller](#7-layer-4--controller)
8. [The MIP Optimization Pipeline](#8-the-mip-optimization-pipeline)
9. [How a Request Travels Through the System](#9-how-a-request-travels-through-the-system)
10. [Key Design Decisions](#10-key-design-decisions)

---

## 1. What is "Software Architecture"?

**Architecture** is the way a software project is organized into separate parts, each with a
clear, specific job. Just as a building has floors, rooms, and structural walls that each serve
a purpose, a software system has layers and components that each serve a purpose.

Good architecture means:
- Each part of the code is responsible for one thing only.
- Parts can be changed or replaced without breaking everything else.
- The code is easier to test, understand, and extend over time.

This project uses an approach called **Clean Architecture** (also known as
**Hexagonal Architecture** or **Ports & Adapters**). The key idea is:

> The core business logic lives in the center and knows nothing about the
> outside world (databases, the internet, third-party libraries).
> Everything that touches the outside world wraps around the center.

A few terms you will see throughout this guide:

- **ABC (Abstract Base Class)** — A Python class that declares method signatures but
  provides no implementation. Think of it as a contract: any class that inherits from the
  ABC *must* implement the declared methods. ABCs live in the `abc` module of Python's
  standard library.

- **Dependency Injection** — Instead of a class creating the things it needs (e.g.,
  instantiating a database connection), those things are *passed in* from the outside.
  This makes it easy to swap real implementations for test doubles.

- **Adapter** — A concrete class that fulfills an abstract interface for a specific
  technology. For example, `FileRequestAdapter` is an adapter that fulfills the
  `BaseDataLoader` interface by reading JSON files from disk.

---

## 2. What is a "Service"?

A **service** is a running program that waits for requests, does some work, and returns a
result. It is similar to a vending machine: you press a button (send a request), it does
something internally, and gives you a result (a response).

This project is a **web service**: it communicates over the internet using a protocol called
**HTTP**. HTTP is the same protocol your web browser uses when it loads a webpage.

In this project, a request says: *"Solve the cargo-loading problem for flight X."*
The response says: *"Here is the recommended cargo selection (or why it couldn't be found)."*

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Redirects to the demo UI |
| `GET` | `/solve/{request_id}` | Solves the cargo optimization for a given request |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | FastAPI auto-generated Swagger UI |

### Response Format

Every response uses the same JSON envelope with a `status` of `SUCCESS` or `FAILURE`:

**Success:**
```json
{
  "recommendation": {
    "selected": [
      {"id": "1", "client_name": "A", "weight_kg": 5000, "volume_m3": 40, "revenue_usd": 10000}
    ],
    "non_selected": [],
    "total_revenue_usd": 10000.0,
    "total_weight_kg": 5000.0,
    "total_volume_m3": 40.0
  },
  "status": "SUCCESS",
  "timestamp": "2026-04-24T20:00:00",
  "message": null
}
```

**Failure:**
```json
{
  "recommendation": null,
  "status": "FAILURE",
  "timestamp": "2026-04-24T20:00:00",
  "message": "Request '999' not found"
}
```

The app entry point is `app/main.py`, which creates the FastAPI app, mounts static files
for the demo UI, provides a root redirect to the UI, and exposes the health endpoint.

---

## 3. The Big Picture: Four Layers

The code is organized into **four layers**. Think of them as four concentric rings — the
innermost ring is the core, and each outer ring adds more connection to the real world.

```
+------------------------------------------------------------------+
|                    CONTROLLER  (app/controller/)                  |
|    HTTP endpoints, JSON schemas, dependency injection wiring      |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |              APPLICATION  (app/application/)             |   |
|   |   Use cases, engine, strategies, abstract interfaces      |   |
|   |                                                          |   |
|   |   +--------------------------------------------------+   |   |
|   |   |              DOMAIN  (app/domain/)               |   |   |
|   |   |    Immutable data models, validation rules       |   |   |
|   |   +--------------------------------------------------+   |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|                 INFRASTRUCTURE  (app/infrastructure/)             |
|    Settings, file loader, DB loader, solver tech adapters         |
+------------------------------------------------------------------+
```

**The Dependency Rule**: Code in an inner ring never imports from an outer ring.
The domain knows nothing about the application layer. The application layer knows
nothing about the controller or infrastructure — it only defines **abstract interfaces**
(also called **ports**) that infrastructure implements with **adapters**.

This is the **Dependency Inversion Principle** in action: high-level policy (application)
depends on abstractions, not on low-level details (infrastructure).

---

## 4. Layer 1 — Domain

**Location**: `app/domain/` · One class per file (project convention).

The domain layer contains **data models** — Python `@dataclass` classes that represent the
cargo optimization problem and its solution. They are pure data containers with built-in
validation. Every domain model uses `frozen=True`, which makes instances **immutable**
(you cannot change their fields after creation). Validation happens in `__post_init__`,
the special method Python calls right after a dataclass is created — this is called
**fail-fast** and prevents bad data from silently propagating.

| Class | File | Purpose |
|-------|------|---------|
| `Aircraft` | `aircraft.py` | Aircraft with weight capacity (kg) and volume capacity (m³). Frozen dataclass. |
| `CargoRequest` | `cargo_request.py` | A single cargo item: id, client name, weight, volume, revenue. Frozen dataclass. |
| `Request` | `request.py` | A full optimization request: one `Aircraft` + a list of `CargoRequest` items. |
| `Recommendation` | `recommendation.py` | The result: lists of selected and non-selected cargo, plus computed totals (revenue, weight, volume). |

**Key principle**: Domain models know nothing about solvers, files, or HTTP. They are the
innermost ring — the purest representation of the business problem.

---

## 5. Layer 2 — Application

**Location**: `app/application/` · This is the "thinking" layer.

The application layer contains the business logic: abstract interfaces that declare *what*
the app needs, the use case that orchestrates a request end-to-end, and the engine/solvers
that actually solve the optimization problem.

### 5.1 Abstract Interfaces (Ports)

A **port** is an abstract interface — a class with method signatures but no implementation.
The application layer defines ports so it can say "I need X" without knowing who provides X.
Infrastructure provides the concrete **adapters** that fulfill these ports.

| Class | File | Contract |
|-------|------|----------|
| `BaseStrategy` | `service/base_strategy.py` | ABC with `solve(Request) -> list[Recommendation]` |
| `BaseDataLoader` | `service/base_data_loader.py` | ABC with `load(request_id) -> Request \| None` |

### 5.2 Use Case & Response

| Class | File | Purpose |
|-------|------|---------|
| `OptimizationService` | `service/optimization_service.py` | The use case: load the request via `BaseDataLoader`, run the `Engine`, wrap the result in an `OptimizationResponse`. |
| `OptimizationResponse` | `service/optimization_response.py` | Result wrapper with `SUCCESS`/`FAILURE` status, timestamp, and optional message. Has `success()` and `failure()` factory methods. |

### 5.3 Engine

| Class | File | Purpose |
|-------|------|---------|
| `Engine` | `engine.py` | Orchestrates: guard validation → strategy selection → solve → business validation. |

The engine picks the strategy based on problem size:
- **≤ 10,000 cargo items** → `MipStrategy` (optimal, exact)
- **> 10,000 cargo items** → `HeuristicStrategy` (fast, approximate)

The threshold is defined by the constant `MAX_CARGO_REQUESTS_FOR_MIP`.

### 5.4 MIP Strategy

The `MipStrategy` follows a three-phase pipeline: **preprocess → optimize → postprocess**.
Each phase is its own class (see [Section 8](#8-the-mip-optimization-pipeline) for the full
walkthrough).

| Class | File | Purpose |
|-------|------|---------|
| `MipStrategy` | `strategy/mip/mip_strategy.py` | Orchestrates the three phases. Implements `BaseStrategy`. |
| `PreProcess` | `strategy/mip/preprocess/preprocess.py` | Partitions cargo into allowed and forbidden sets. |
| `PreProcessedData` | `strategy/mip/preprocess/pre_processed_data.py` | Data container holding the preprocessed cargo partitions. |
| `Optimization` | `strategy/mip/optimization/optimization.py` | Builds a Pyomo model, solves it, extracts the recommendation. |
| `PostProcess` | `strategy/mip/postprocess/postprocess.py` | Post-processing extension point (currently pass-through). |

### 5.5 Heuristic Strategy

| Class | File | Purpose |
|-------|------|---------|
| `HeuristicStrategy` | `strategy/heuristic/heuristic_strategy.py` | Greedy algorithm: sorts cargo by revenue descending, packs items until weight or volume is exhausted. Implements `BaseStrategy`. |

### 5.6 Solver Technology Abstractions

The MIP model is built with **Pyomo** (a Python optimization modeling library), but the
actual solver engine that crunches the numbers is pluggable:

| Class | File | Purpose |
|-------|------|---------|
| `BaseTechnologySolver` | `solvers/base_technology_solver.py` | ABC for solver technology adapters. |
| `HighsSolver` | `solvers/highs_solver.py` | Adapter for **HiGHS** — an open-source LP/MIP solver (the default). |
| `XpressSolver` | `solvers/xpress_solver.py` | Adapter for **FICO Xpress** (placeholder for future use). |

To add a new solver engine (e.g., Gurobi), create a new class that implements
`BaseTechnologySolver` — no changes needed to the model-building code.

---

## 6. Layer 3 — Infrastructure

**Location**: `app/infrastructure/`

The infrastructure layer contains **concrete implementations** of the abstract interfaces
defined in the application layer, plus configuration. This is where the outside world
(files, databases, environment variables) is accessed.

| Class | File | Purpose |
|-------|------|---------|
| `Settings` | `config/settings.py` | Loads configuration from environment variables (prefix `OPT_`) using **Pydantic Settings**. |
| `FileRequestAdapter` | `data_loaders/file_data_loader.py` | Implements `BaseDataLoader`. Reads `data/{request_id}/data.json` from disk. |
| `DbRequestAdapter` | `data_loaders/db_data_loader.py` | Implements `BaseDataLoader`. Database loader (placeholder for future use). |

### Data Files

Request data lives in `data/{request_id}/data.json` with camelCase JSON keys:

```json
{
  "requestId": "1",
  "aircraft": {
    "tailNumber": "3AA",
    "maxWeightKg": 20000,
    "maxVolumeM3": 150
  },
  "cargoRequests": [
    {"id": "1", "clientName": "A", "weightKg": 5000, "volumeM3": 40, "revenueUsd": 10000}
  ]
}
```

### How to Extend

**Add a new data source** (e.g., a real database):
1. Create a class in `app/infrastructure/data_loaders/` that inherits from `BaseDataLoader`.
2. Implement the `load(request_id) -> Request | None` method.
3. Wire it into `app/controller/dependencies.py` so FastAPI injects it.

**Add a new solver technology** (e.g., Gurobi):
1. Create a class in `app/application/strategy/mip/optimization/solvers/` that inherits from `BaseTechnologySolver`.
2. Implement the required methods.
3. The `Optimization` class can then use it — no changes to the Pyomo model needed.

---

## 7. Layer 4 — Controller

**Location**: `app/controller/`

The controller layer is the **front door** — it handles everything HTTP-related and wires
the application together using **dependency injection**.

### What is Dependency Injection?

Instead of the `solve` endpoint creating its own `FileRequestAdapter` and `Engine`, those
objects are *injected* by FastAPI's dependency system (configured in `dependencies.py`).
This means:
- The endpoint code is short and focused on HTTP concerns.
- You can swap `FileRequestAdapter` for `DbRequestAdapter` by changing one line in
  `dependencies.py` — no endpoint code changes.
- Tests can inject mock implementations easily.

### Components

| Component | File | Purpose |
|-----------|------|---------|
| `solve` endpoint | `routes/optimization.py` | `GET /solve/{request_id}` — receives the request ID, calls `OptimizationService`, returns the response. |
| Dependency wiring | `dependencies.py` | Configures which concrete classes to inject (data loader, solvers, engine, service). |
| `OptimizationResponseSchema` | `schemas/optimization_response_schema.py` | Pydantic model defining the JSON shape of the full response. |
| `RecommendationSchema` | `schemas/recommendation_schema.py` | Pydantic model for the recommendation portion of the response. |
| `CargoRequestSchema` | `schemas/cargo_request_schema.py` | Pydantic model for individual cargo items in the response. |

### Demo UI

The app includes a simple demo interface served as static files:

- `app/static/index.html` — Landing page built with Bootstrap 5 and jQuery.
- `app/static/app.js` — Fetches `GET /solve/{requestId}` and displays the JSON result.

All vendor libraries (Bootstrap, jQuery) are bundled locally — **no CDN calls**, so the
demo works offline or in air-gapped environments.

---

## 8. The MIP Optimization Pipeline

This section walks through the mathematical optimization in detail. If you are familiar
with mixed-integer programming, this will feel like home. If not, each piece is explained.

### 8.1 Pipeline Overview

When the `MipStrategy` is selected (problems with ≤ 10,000 cargo items), it runs three
phases:

```
Request
  │
  ▼
PreProcess ──── Partition cargo into "allowed" and "forbidden" sets
  │
  ▼
Optimization ── Build Pyomo model → solve with HiGHS → extract recommendation
  │
  ▼
PostProcess ─── Extension point (pass-through today)
  │
  ▼
Recommendation
```

### 8.2 PreProcess

**Class**: `PreProcess` in `strategy/mip/preprocess/preprocess.py`

The preprocessor examines each `CargoRequest` and partitions the list into two groups:
- **Allowed** — cargo that is eligible to be loaded.
- **Forbidden** — cargo that must be excluded (e.g., exceeds aircraft capacity on its own).

The result is stored in a `PreProcessedData` container that the optimization phase
consumes.

### 8.3 The Pyomo Model — Component by Component

**Class**: `Optimization` in `strategy/mip/optimization/optimization.py`

The optimization phase builds a **Pyomo `ConcreteModel`** — a mathematical program — by
adding components one at a time. Each component is its own class in the `components/`
directory. This keeps the math modular: you can add a new constraint by creating one file
without touching the others.

#### Sets

- **I** — the set of allowed cargo items (indexed by cargo ID).
- **C** — the set of unique clients.
- **I_c** — for each client *c*, the subset of cargo items belonging to that client.
- **I_f** — the set of forbidden cargo items.

#### Decision Variables

| Class | File | Math | Meaning |
|-------|------|------|---------|
| `VariableSelectCargo` | `variable_select_cargo.py` | x_i ∈ {0, 1}  ∀ i ∈ I | 1 if cargo item *i* is loaded, 0 otherwise. |
| `VariableSelectClient` | `variable_select_client.py` | y_c ∈ {0, 1}  ∀ c ∈ C | 1 if at least one item from client *c* is loaded. |

#### Constraints

| Class | File | Math | Meaning |
|-------|------|------|---------|
| `ConstraintLimitWeight` | `constraint_limit_weight.py` | ∑ w_i · x_i ≤ W | Total weight of selected cargo must not exceed aircraft weight capacity *W*. |
| `ConstraintLimitVolume` | `constraint_limit_volume.py` | ∑ v_i · x_i ≤ V | Total volume of selected cargo must not exceed aircraft volume capacity *V*. |
| `ConstraintForbidCargo` | `constraint_forbid_cargo.py` | x_i = 0  ∀ i ∈ I_f | Forbidden cargo items are forced to zero. |
| `ConstraintClientImpliesCargo` | `constraint_client_implies_cargo.py` | y_c ≤ x_i  ∀ c ∈ C, i ∈ I_c | A client can only be "selected" if *all* of that client's cargo items are loaded. This links the client variable to its cargo variables. |

#### Objective Function

| Class | File | Math |
|-------|------|------|
| `ObjectiveRevenue` | `objective_revenue.py` | α · ∑ r_i · x_i |
| `ObjectiveClientDiversity` | `objective_client_diversity.py` | β · ∑ y_c |

The **combined objective** to maximize is:

```
maximize   α · ∑ r_i · x_i   +   β · ∑ y_c
           ─────────────────       ─────────
           revenue term            client diversity bonus
```

The weights α and β let you tune the trade-off between maximizing revenue and spreading
load across more clients.

### 8.4 Solver Technology Layer

Once the Pyomo model is built, it needs an actual solver engine to find the optimal
solution. The `BaseTechnologySolver` ABC provides a clean boundary:

```
Pyomo Model  ──▶  BaseTechnologySolver  ──▶  Solution
                        │
                  ┌─────┴─────┐
                  ▼           ▼
             HighsSolver   XpressSolver
             (default)     (placeholder)
```

- **HiGHS** is an open-source, high-performance LP/MIP solver — it is the default and
  requires no commercial license.
- **FICO Xpress** is a commercial solver — the adapter exists as a placeholder for teams
  that have an Xpress license.

To add a new solver engine (e.g., Gurobi, CPLEX), create a new adapter that inherits
from `BaseTechnologySolver`. The Pyomo model-building code does not change at all.

### 8.5 PostProcess

**Class**: `PostProcess` in `strategy/mip/postprocess/postprocess.py`

Currently a pass-through. This phase exists as an **extension point** — if you later need
to enrich the recommendation (e.g., add cost breakdowns or reorder selected cargo), this
is where that logic goes without touching the optimization phase.

---

## 9. How a Request Travels Through the System

Here is the full journey of a `GET /solve/1` request:

```
Client (GET /solve/1)
  │
  ▼
Controller ─── routes/optimization.py
  │            Receives request_id, calls OptimizationService
  │
  ▼
Application ── OptimizationService (use case)
  │            Calls BaseDataLoader.load() then Engine.run()
  │
  ├──▶ BaseDataLoader.load("1")
  │    (abstract interface → FileRequestAdapter reads data/1/data.json)
  │
  ▼
Application ── Engine
  │            Guard validation → strategy selection → solve → business validation
  │
  │   ┌─── Problem size ≤ 10,000? ───┐
  │   │ YES                          │ NO
  │   ▼                              ▼
  │  MipStrategy.solve()         HeuristicStrategy.solve()
  │   │                              │
  │   ├── PreProcess                 └── Greedy selection by revenue
  │   │   partition cargo
  │   │
  │   ├── Optimization
  │   │   build Pyomo model
  │   │   solve with HiGHS
  │   │   extract recommendation
  │   │
  │   └── PostProcess
  │       (extension point)
  │
  ▼
Application ── OptimizationResponse.success() or .failure()
  │            Wraps result with status, timestamp, message
  │
  ▼
Controller ─── OptimizationResponseSchema
  │            Serializes to JSON
  │
  ▼
Client (JSON response)
```

**Step by step:**

1. **Client** sends `GET /solve/1`.
2. **Controller** (`routes/optimization.py`) receives `request_id = "1"` and calls
   `OptimizationService`.
3. **OptimizationService** calls `BaseDataLoader.load("1")`. At runtime this is
   `FileRequestAdapter`, which reads `data/1/data.json` and returns a `Request` domain
   object (or `None` if the file doesn't exist).
4. If the request was loaded, the service calls `Engine.run(request)`.
5. **Engine** performs guard validation, then selects `MipStrategy` or `HeuristicStrategy`
   based on the number of cargo items.
6. The selected **strategy** produces a `Recommendation` (selected + non-selected cargo
   with totals).
7. **Engine** performs business validation on the result, then returns it.
8. **OptimizationService** wraps the result in an `OptimizationResponse` with
   `status = "SUCCESS"` and a timestamp (or `"FAILURE"` with an error message).
9. **Controller** serializes the response through `OptimizationResponseSchema` and returns
   JSON to the client.

---

## 10. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **4 layers** (domain → application → infrastructure → controller) | Matches the Java template this project is ported from; clear separation of concerns. |
| **Abstract interfaces (ports) in the application layer** | The application declares what it needs; infrastructure provides it. This is Dependency Inversion — high-level code never depends on low-level details. |
| **Engine with strategy selection** | MIP gives optimal solutions on smaller problems; the heuristic provides speed on larger ones. The engine picks automatically. |
| **One class per file** | Keeps each file focused and easy to navigate. This is a project convention, not a Python requirement. |
| **Frozen dataclasses in domain** | Immutability prevents accidental modification of domain data. Validation in `__post_init__` catches bad data immediately (fail-fast). |
| **Solver technology abstraction** (`BaseTechnologySolver`) | Lets you swap HiGHS for Xpress, Gurobi, or CPLEX without changing a single line of the Pyomo model-building code. |
| **Component-based model building** | Each variable, constraint, and objective is a separate class in its own file. This makes the math modular, testable, and easy to extend. |
| **Preprocess → optimize → postprocess** | Isolates data preparation, mathematical solving, and result enrichment into separate phases. Each phase can be tested and evolved independently. |
| **Response wrapper with `success()`/`failure()` factories** | Uniform JSON envelope for all responses. The API never throws HTTP exceptions to the client — errors are reported in the response body. |
| **Vendor libs served locally (no CDN)** | The demo UI works without internet access — important for air-gapped or restricted environments. |
| **No authentication** | This is a template meant to be extended. Adopters add their own auth layer (OAuth, API keys, etc.) as needed. |