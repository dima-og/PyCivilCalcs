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

## 9) Control equation alignment and numbering

```python
# defaults for this environment
v = EngEnv(eq_numbers=True, center_equations=False, eq_start=0)

# override per equation
v.eq.M_n.show(number=True, center=False)
v.eq.M_n.show(number=True, tag='@MnFlexure')
```

Use `v.reset_eq(0)` to restart automatic numbering.


## 10) Optional pure-LaTeX notebook mode (no HTML wrappers)

```python
v = EngEnv(auto_display=True, notebook_render_mode='latex')
v.eq.M_n = 'F_y * Z_x'
v.eq.M_n.show(center=True)
```

### Greek symbol definitions used by name rendering

Use these ASCII prefixes in variable/equation names to get Greek symbols in output (for example, `phi_n` renders as `\phi_{n}`):

| ASCII name | Rendered symbol | Example name |
|---|---|---|
| `alpha` | `\alpha` | `alpha_v` |
| `beta` | `\beta` | `beta_1` |
| `gamma` | `\gamma` | `gamma_c` |
| `delta` / `Delta` | `\delta` / `\Delta` | `Delta_P` |
| `theta` / `Theta` | `\theta` / `\Theta` | `theta_n` |
| `lambda` / `Lambda` | `\lambda` / `\Lambda` | `lambda_b` |
| `mu` | `\mu` | `mu_f` |
| `phi` / `Phi` | `\phi` / `\Phi` | `phi_n` |
| `psi` / `Psi` | `\psi` / `\Psi` | `psi_t` |
| `omega` / `Omega` | `\omega` / `\Omega` | `omega_u` |
| `rho` | `\rho` | `rho_s` |
| `sigma` / `Sigma` | `\sigma` / `\Sigma` | `sigma_cr` |
| `tau` | `\tau` | `tau_v` |
| `xi` / `Xi` | `\xi` / `\Xi` | `xi_b` |
| `pi` / `Pi` | `\pi` / `\Pi` | `pi_0` |

You can also use direct Unicode names such as `ΔP` via `v.eq.define('ΔP', 'rho * g * h')`.

## 11) Greek symbols and non-attribute equation names

```python
# ASCII names render as Greek in LaTeX output when applicable
v.eq.phi_n = 'phi * M_n'
v.phi = 0.9
v.eq.phi_n.show()

# For names that are not valid Python identifiers, use define + indexing
v.eq.define('ΔP', 'rho * g * h')
v.rho = (62.4, 'lbf/ft^3')
v.g = 1
v.h = (10, 'ft')
v.eq['ΔP'].show()
```
