# SEFOP - python

**Reference implementation of the [SEFOP framework](https://github.com/fjzs/sefop) for Python**

> This is the **Python implementation** of SEFOP (v1.0).
> For the theory, motivation, and language-agnostic design of the framework, see the main repository: [github.com/fjzs/sefop](https://github.com/fjzs/sefop).

---

## Who this is for

| Background | What you will get from this repo |
|---|---|
| OR practitioner / data scientist | A template for adding automated testing to your optimization projects |
| Software engineer | A concrete example of Clean Architecture applied to a non-trivial domain |
| Researcher / academic | A reproducible reference implementation to cite or build upon |

---

## Repository structure

```
src/knapsack/
├── domain/       # Pure Python. No solver. Entities and value objects.
├── model/        # Builds variables, constraints, and objective. No solver.
├── application/  # Orchestrates model building and solving.
└── infrastructure/  # PuLP adapter + CLI. Solver lives here only.

tests/
├── unit/         # ATOM unit tests — one file per model component
└── integration/  # ATOM integration tests — compare against saved oracles
```

The key rule: **`domain/` and `model/` import nothing outside the Python standard library.** This is what makes ATOM testing possible.

---

## Part of the SEFOP ecosystem

| Repository | Purpose |
|---|---|
| [sefop](https://github.com/fjzs/sefop) | Theory, motivation, and language-agnostic framework design |
| **sefop-python** ← you are here | Python reference implementation (v1.0) |
| sefop-java *(coming soon)* | Java reference implementation |

---

## Installation instructions

1. Clone the repository:
   ```
   git clone
    ```
2. Navigate to the project directory.
3. Create a virtual environment with python 3.12 and activate it:
   ```
   py -3.12 -m venv .venv
   source venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```
5. Run the tests, they all should pass:
    ```
    pytest
    ```