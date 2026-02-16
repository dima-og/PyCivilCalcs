# PyCivilCalcs Tutorial

This tutorial shows a practical workflow for structural calculations:

1. Define the equation first (symbolic template).
2. Validate required variables and units.
3. Define variables silently.
4. Evaluate and print symbolic / numeric / full output.

## 1) Create the environment

```python
from re_lib.eng_var import EngEnv

v = EngEnv(auto_display=False)
```

## 2) Define equation first

```python
phi_mn = v.equation("phi_M_n = phi_b * F_y * Z_x")
phi_mn.show_calcs(view="sym")
```

This is useful when preparing report-ready equations before final values are known.

## 3) Validate missing inputs and expected units

```python
report = v.validate(
    phi_mn,
    required_vars={
        "phi_b": "dimensionless",
        "F_y": "ksi",
        "Z_x": "in^3",
    },
    expected_units="kip*in",
)
print(report.valid)
print(report.message())
```

## 4) Define variables silently

```python
v.define("phi_b", 0.9, show=False)
v.define("F_y", 50, "ksi", comment="A992 steel", show=False)
v.define("Z_x", 120, "in^3", comment="Section plastic modulus", show=False)
```

You can later edit metadata:

```python
v.Z_x.units = "cm^3"
v.Z_x.comment = "Converted for SI check"
```

## 5) Evaluate equation

```python
# Numeric substitution + result
phi_mn.show_calcs(view="num", out_units="kip*in")

# Symbolic + numeric chain in one line
phi_mn.show_calcs(view="full", out_units="kip*ft")
```

## 6) Reuse with overrides for design studies

```python
phi_mn(phi_b=0.85 * v.dimensionless).show_calcs(view="num", out_units="kip*in")
```

## Tips for AI-assisted workflows

- Store equation templates in standalone Python modules and import them into calc notebooks.
- Call `validate(...)` before final `show_calcs(...)` to catch missing variables or wrong unit intent.
- Use `define(..., show=False)` to keep notebooks clean while still tracking metadata.
