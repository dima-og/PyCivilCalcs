# PyCivilCalcs

PyCivilCalcs is a lightweight engineering-calculation toolkit built around:

- `pint` for unit-safe arithmetic,
- `sympy` for symbolic display,
- notebook-friendly equation rendering.

It is designed for structural engineering calculations and workflows that can be reused by both engineers and AI agents.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from re_lib.eng_var import EngEnv

v = EngEnv(auto_display=False)

# 1) Define equation first
mn = v.equation("M_n = F_y * Z_x")
mn.show_calcs(view="sym")

# 2) Validate before assigning values
report = v.validate(
    mn,
    required_vars={"F_y": "ksi", "Z_x": "in^3"},
    expected_units="kip*in",
)
print(report.message())

# 3) Define variables silently
v.define("F_y", 50, "ksi", comment="Yield strength", show=False)
v.define("Z_x", 100, "in^3", comment="Plastic section modulus", show=False)

# 4) Evaluate numerically
mn.show_calcs(view="num", out_units="kip*in")
```

## Core Features

- **Symbolic-first equations** (`equation` / `expr`) so formulas can be shown before values.
- **Silent variable definition** (`define(..., show=False)`) for clean notebooks.
- **Editable metadata** on variables:
  - `var.units` to convert units,
  - `var.comment` to update comments.
- **Validation** with `validate(...)`:
  - missing variable detection,
  - per-variable expected unit checks,
  - optional result-unit compatibility checks.

## Tutorial

See [`docs/tutorial.md`](docs/tutorial.md) for a step-by-step workflow including validation and reusable equation templates.

## Testing

```bash
python -m unittest discover -s tests -v
```
