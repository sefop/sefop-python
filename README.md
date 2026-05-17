# SEFOP - Python Starter

**Reference implementation of [SEFOP](https://github.com/sefop) for Python**

[![License: MIT](https://opensource.org/licenses/MIT)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](#testing)
[![Discussions](https://img.shields.io/badge/discussions-active-blue)](https://github.com/sefop/discussions)

---

## Repository structure

```
src/
  domain/               # pure entities — no imports from other folders
  services/             # orchestration + data loading
  optimization/         # solving logic
  dependencies.py       # composition root
  cli.py                # CLI entry point
tests/                  # automatic tests
data/                   # sample instances
docs/                   # guides and documentation
```

---

## Installation

Clone the repository:
```bash
git clone https://github.com/sefop/sefop-python-starter.git
cd sefop-python-starter
```

Create a virtual environment with Python 3.12 and activate it:
```bash
py -3.12 -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Testing

Run all tests:
```bash
pytest
```

Run tests by layer:
```bash
pytest tests/domain/          # domain unit tests only
pytest tests/services/        # service tests only
pytest tests/optimization/    # optimization + MIP tests
```

---

## Usage

Solve a knapsack optimization request:
```bash
python -m cli 1  # solve request from data/1/data.json
python -m cli 2  # solve request from data/2/data.json
```

---

