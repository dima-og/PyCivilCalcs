# PyCivilCalcs

PyCivilCalcs is a unit-aware engineering calculation toolkit for structural workflows.

## Installation

```bash
pip install -r requirements.txt
```

## Core API

- Define equations in an equation namespace:
  - `v.eq.M_n = 'F_y * Z_x'`
- Define variables by assignment:
  - `v.F_t = 20`
  - `v.F_t = (20, 'ksi')`
  - `v.F_t = (20, 'ksi', 'Rupture modulus')`
  - `v.F_t = (20, 'ksi', 'Rupture modulus', True)`  (`show` override)
- Display variables explicitly:
  - `v.F_t.show()`
- Display equations:
  - `expr.show()` (default: symbolic if missing vars, numeric if all vars exist)
  - `expr.show(view='sym'|'num'|'full')`
- Return only the numeric value:
  - `expr.value()`
  - `expr.value('kip*in')`

## Quick Start

```python
from re_lib.eng_var import EngEnv

v = EngEnv(auto_display=False)

# Define equation first
v.eq.M_n = 'F_y * Z_x'

# Show symbolic by default (variables missing)
v.eq.M_n.show()

# Define variables
v.F_y = (50, 'ksi', 'Yield strength')
v.Z_x = (100, 'in^3', 'Plastic modulus')

# Now show() defaults to numeric (all vars available)
v.eq.M_n.show(out_units='kip*in')

# Numeric magnitude only
mn = v.eq.M_n.value('kip*in')
print(mn)
```

## Notes

- Unit consistency is handled by `pint` arithmetic and conversions.
- Old API names (`show_calcs`, `define`) are still available as compatibility aliases.

## Tutorial

See [`docs/tutorial.md`](docs/tutorial.md).

## Testing

```bash
python -m unittest discover -s tests -v
```
