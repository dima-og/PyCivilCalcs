# PyCivilCalcs Tutorial

## 1) Create environment

```python
from re_lib.eng_var import EngEnv

v = EngEnv(auto_display=False)
```

## 2) Define equation first with `eq`

```python
v.eq.M_n = 'F_y * Z_x'
```

This creates a reusable equation object at `v.eq.M_n`.

## 3) Show equation before values are defined

```python
# Defaults to symbolic because variables are not defined yet
v.eq.M_n.show()
```

## 4) Define variables using assignment forms

```python
v.F_y = (50, 'ksi', 'Yield strength')
v.Z_x = (100, 'in^3', 'Plastic modulus')

# Also supported:
v.F_t = 20
v.F_t = (20, 'ksi')
v.F_t = (20, 'ksi', 'Rupture modulus')
v.F_t = (20, 'ksi', 'Rupture modulus', True)
```

- The 4th tuple item controls one-time print behavior for that assignment.

## 5) Display variables directly

```python
v.F_y.show()
v.Z_x.show()
```

## 6) Evaluate equation

```python
# Defaults to numeric now (all variables exist)
v.eq.M_n.show(out_units='kip*in')

# Force explicit views if needed
v.eq.M_n.show(view='sym')
v.eq.M_n.show(view='num', out_units='kip*in')
v.eq.M_n.show(view='full', out_units='kip*in')
```

## 7) Return value only

```python
mn = v.eq.M_n.value('kip*in')
print(mn)  # float magnitude only
```

## 8) Reusable templates from files

For larger projects, store equations in separate modules and assign them into `v.eq.*` in calc notebooks/scripts.
