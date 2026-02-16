# re_lib/eng_var.py
# pip install pint sympy

from __future__ import annotations

import keyword
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pint
from pint.errors import DimensionalityError, UndefinedUnitError

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from sympy.printing.latex import latex as sp_latex

# Notebook math rendering (no HTML)
try:
    from IPython.display import display, Math  # type: ignore
except Exception:  # pragma: no cover
    def display(x):  # type: ignore
        print(x)

    class Math(str):  # type: ignore
        pass


__all__ = ["ureg", "Q_", "EngVar", "ValidationReport", "EngEnv", "CalcExpr"]


# ----------------------------
# Unit registry (shared)
# ----------------------------
ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity

# Common engineering aliases (define if missing)
try:
    ureg.Unit("ksi")
except Exception:
    ureg.define("ksi = 1000 * psi = ksi")

try:
    ureg.Unit("kip")
except Exception:
    ureg.define("kip = 1000 * pound_force = kip")


# ----------------------------
# LaTeX helpers for Pint
# ----------------------------
def _unit_to_latex(u: pint.Unit) -> str:
    s = f"{u:~P}"  # abbreviated pretty units
    s = s.replace("**", "^")
    s = s.replace(" / ", r"\,/\,")

    # guard against unicode squares if they appear
    s = s.replace("in²", "in^2").replace("ft²", "ft^2")

    return r"\mathrm{" + s.replace(" ", r"\,") + "}"


def _qty_to_latex(q: pint.Quantity, fmt: str = "g") -> str:
    mag = q.magnitude
    try:
        mag_s = format(mag, fmt)
    except Exception:
        mag_s = str(mag)

    if q.dimensionless or str(q.units) in ("dimensionless", "1"):
        return mag_s

    return mag_s + r"\," + _unit_to_latex(q.units)


def _escape_latex_text(s: str) -> str:
    return (
        s.replace("\\", r"\textbackslash ")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("$", r"\$")
    )


# ----------------------------
# Protect numeric literals (prevents folding like 0.85/2 -> 0.425)
# ----------------------------
_NUM_RE = re.compile(r"(?<![\w.])(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?(?![\w.])")




def _extract_symbol_names(expr: str) -> set[str]:
    names = set(re.findall(r"\b[A-Za-z]\w*\b", expr))
    reserved = {"math", "pi"} | set(keyword.kwlist) | set(dir(math))
    return {name for name in names if name not in reserved}

def _protect_numeric_literals(expr: str):
    mapping: Dict[sp.Symbol, str] = {}
    i = 0

    def repl(m: re.Match):
        nonlocal i
        lit = m.group(0)
        sym = sp.Symbol(f"CONST{i}")  # avoid "_" prefix
        i += 1
        mapping[sym] = lit
        return str(sym)

    return _NUM_RE.sub(repl, expr), mapping


# ----------------------------
# Core variable container
# ----------------------------
@dataclass
class EngVar:
    quantity: pint.Quantity
    desc: str = ""

    @property
    def units(self) -> str:
        return str(self.quantity.units)

    @units.setter
    def units(self, new_units: str):
        self.quantity = self.quantity.to(new_units)

    @property
    def comment(self) -> str:
        return self.desc

    @comment.setter
    def comment(self, text: str):
        self.desc = text

    def latex(self, fmt: str = "g") -> str:
        return _qty_to_latex(self.quantity, fmt=fmt)

    def to(self, units: str) -> "EngVar":
        self.quantity = self.quantity.to(units)
        return self

    def __str__(self) -> str:
        return self.latex()

    def __format__(self, format_spec: str) -> str:
        return self.latex(fmt=format_spec or "g")


@dataclass
class ValidationReport:
    valid: bool
    missing_vars: list[str]
    unit_errors: list[str]
    result_units: str | None = None

    def message(self) -> str:
        pieces: list[str] = []
        if self.missing_vars:
            pieces.append(f"Missing variables: {', '.join(self.missing_vars)}")
        if self.unit_errors:
            pieces.extend(self.unit_errors)
        return "\n".join(pieces) if pieces else "Validation passed."


# ----------------------------
# Callable calc object
# ----------------------------
class CalcExpr:
    def __init__(
        self,
        env: "EngEnv",
        lhs: str,
        rhs: str,
        out_units: str | None = None,
        fmt: str = "g",
        length_unit: str | None = None,
        tag: str | int | None = None,
        store: bool = True,
        overrides: Optional[Dict[str, pint.Quantity]] = None,
    ):
        self.env = env
        self.lhs = lhs
        self.rhs = rhs
        self.out_units = out_units
        self.fmt = fmt
        self.length_unit = length_unit
        self.tag = tag
        self.store = store
        self.overrides: Dict[str, pint.Quantity] = overrides or {}
        self.quantity: Optional[pint.Quantity] = None

        self._number_default: bool = False
        self._center_default: bool = True

    def __call__(self, **overrides: pint.Quantity) -> "CalcExpr":
        merged = dict(self.overrides)
        merged.update(overrides)
        nxt = CalcExpr(
            env=self.env,
            lhs=self.lhs,
            rhs=self.rhs,
            out_units=self.out_units,
            fmt=self.fmt,
            length_unit=self.length_unit,
            tag=self.tag,
            store=self.store,
            overrides=merged,
        )
        nxt._number_default = self._number_default
        nxt._center_default = self._center_default
        return nxt

    def eval(self) -> pint.Quantity:
        local_ns: Dict[str, Any] = {"math": math}

        for name, v in self.env._vars.items():
            local_ns[name] = v.quantity
        for k, q in self.overrides.items():
            local_ns[k] = q

        try:
            result = eval(self.rhs, {"__builtins__": {}}, local_ns)
        except NameError as e:
            msg = str(e)
            m = re.search(r"name '([^']+)' is not defined", msg)
            missing = m.group(1) if m else msg

            defined = sorted(self.env._vars.keys())
            defined_s = ", ".join(defined) if defined else "(none)"
            ov = sorted(self.overrides.keys())
            ov_s = ", ".join(ov) if ov else "(none)"

            raise NameError(
                f"Missing variable '{missing}' in expression: {self.rhs}\n"
                f"Defined in env: {defined_s}\n"
                f"Overrides on this CalcExpr: {ov_s}\n"
                f"Fix: define it first, e.g. v.{missing} = (value, 'units')"
            ) from e

        if self.out_units is not None:
            result = result.to(self.out_units)

        self.quantity = result
        return result

    def _build_symbolic(self) -> sp.Expr:
        rhs_sym = self.rhs.replace("math.pi", "pi")
        rhs_sym, const_map = _protect_numeric_literals(rhs_sym)

        sym_locals: Dict[str, Any] = {"pi": sp.pi}
        name_tokens = _extract_symbol_names(rhs_sym)
        for name in name_tokens:
            if name in {"math", "pi"}:
                continue
            sym_locals[name] = sp.Symbol(name)

        for csym in const_map.keys():
            sym_locals[str(csym)] = csym

        sym = parse_expr(rhs_sym, local_dict=sym_locals, transformations=standard_transformations, evaluate=False)

        sym2 = sym
        for csym, lit in const_map.items():
            sym2 = sym2.xreplace({csym: sp.Symbol(lit)})
        return sym2

    def variable_names(self) -> set[str]:
        return _extract_symbol_names(self.rhs.replace("math.pi", "pi"))

    def validate(
        self,
        required_vars: Dict[str, str] | list[str] | None = None,
        expected_units: str | None = None,
        overrides: Optional[Dict[str, pint.Quantity]] = None,
        raise_on_error: bool = False,
    ) -> ValidationReport:
        merged_overrides = dict(self.overrides)
        if overrides:
            merged_overrides.update(overrides)

        required = self.variable_names()
        defined = set(self.env._vars.keys()) | set(merged_overrides.keys())
        missing = sorted(required - defined)

        req_unit_map: Dict[str, str | None] = {}
        if isinstance(required_vars, dict):
            req_unit_map.update(required_vars)
        elif isinstance(required_vars, list):
            for n in required_vars:
                req_unit_map[n] = None

        unit_errors: list[str] = []
        for name, req_unit in req_unit_map.items():
            if name not in defined:
                if name not in missing:
                    missing.append(name)
                continue
            if req_unit is None:
                continue
            q = merged_overrides.get(name, self.env._vars[name].quantity)
            try:
                q.to(req_unit)
            except DimensionalityError:
                unit_errors.append(
                    f"Variable '{name}' with units '{q.units}' is not compatible with expected '{req_unit}'."
                )

        result_units: str | None = None
        if not missing:
            try:
                q_eval = self(**merged_overrides).eval()
                result_units = str(q_eval.units)
                if expected_units is not None:
                    q_eval.to(expected_units)
            except DimensionalityError:
                unit_errors.append(
                    f"Expression result units '{result_units or 'unknown'}' are not compatible with expected '{expected_units}'."
                )
            except Exception as exc:
                unit_errors.append(f"Validation evaluation failed: {exc}")

        missing = sorted(set(missing))
        report = ValidationReport(valid=(not missing and not unit_errors), missing_vars=missing, unit_errors=unit_errors, result_units=result_units)
        if raise_on_error and not report.valid:
            raise ValueError(report.message())
        return report

    def show_calcs(
        self,
        view: str = "full",          # "full" | "num" | "sym"
        out_units: str | None = None,
        fmt: str | None = None,
        length_unit: str | None = None,
        tag: str | int | None = None,
        store: bool | None = None,
        number: bool | None = None,
        center: bool | None = None,
    ) -> pint.Quantity:
        if view not in ("full", "num", "sym"):
            raise ValueError("view must be one of: 'full', 'num', 'sym'")

        out_units = self.out_units if out_units is None else out_units
        fmt = self.fmt if fmt is None else fmt
        length_unit = self.length_unit if length_unit is None else length_unit
        store = self.store if store is None else store

        if number is None:
            number = self._number_default
        if center is None:
            center = self._center_default
        if tag is None:
            tag = self.tag

        result: pint.Quantity | None = None
        if view != "sym":
            result = self.eval()

            if out_units is not None:
                try:
                    result = result.to(out_units)
                except DimensionalityError as e:
                    raise DimensionalityError(e.units1, e.units2, f"Cannot convert result to '{out_units}'.") from e
                self.quantity = result

        if length_unit is None:
            length_unit = str(self.env._vars["r"].quantity.units) if "r" in self.env._vars else "in"

        def display_qty(q: pint.Quantity) -> pint.Quantity:
            try:
                if q.check("[length]"):
                    return q.to(length_unit)  # type: ignore[arg-type]
            except Exception:
                pass
            if out_units is not None:
                try:
                    return q.to(out_units)
                except DimensionalityError:
                    pass
            return q

        sym2 = self._build_symbolic()

        latex_sym = sp_latex(sym2, mul_symbol="dot")
        symbol_names: Dict[sp.Symbol, str] = {}
        for name, v in self.env._vars.items():
            symbol_names[sp.Symbol(name)] = rf"\left({EngVar(display_qty(v.quantity)).latex(fmt=fmt)}\right)"
        for name, q in self.overrides.items():
            symbol_names[sp.Symbol(name)] = rf"\left({EngVar(display_qty(q)).latex(fmt=fmt)}\right)"

        latex_sub = sp_latex(sym2, mul_symbol="dot", symbol_names=symbol_names)
        res_latex = EngVar(result).latex(fmt=fmt) if result is not None else ""

        lhs = self.lhs
        if view == "sym":
            eq = rf"{lhs} = {latex_sym}" if lhs else latex_sym
        elif view == "num":
            eq = rf"{lhs} = {latex_sub} = {res_latex}" if lhs else rf"{latex_sub} = {res_latex}"
        else:
            eq = rf"{lhs} = {latex_sym} = {latex_sub} = {res_latex}" if lhs else rf"{latex_sym} = {latex_sub} = {res_latex}"

        # numbering: append visible text number (no \tag)
        if number:
            if tag is None:
                tag = "auto"
            if tag == "auto":
                n = self.env.next_eq()
            elif isinstance(tag, str) and tag.startswith("@"):
                n = self.env.next_eq(label=tag[1:])
            else:
                n = tag
            eq += rf"\qquad\text{{({n})}}"

        self.env.render_equation(eq, center=center)

        if store and lhs and result is not None:
            prev = self.env._auto_display
            self.env._auto_display = False
            try:
                setattr(self.env, lhs, EngVar(result))
            finally:
                self.env._auto_display = prev

        return result  # type: ignore[return-value]


# ----------------------------
# Environment / namespace
# ----------------------------
class EngEnv:
    def __init__(
        self,
        unit_registry: pint.UnitRegistry = ureg,
        auto_display: bool = True,
        eq_numbers: bool = False,
        center_equations: bool = True,
        eq_start: int = 0,
        output: str = "notebook",   # "notebook" or "asis" (Quarto/PDF)
    ):
        object.__setattr__(self, "_ureg", unit_registry)
        object.__setattr__(self, "_auto_display", auto_display)
        object.__setattr__(self, "_vars", {})  # type: Dict[str, EngVar]

        object.__setattr__(self, "_eq_numbers", eq_numbers)
        object.__setattr__(self, "_center_equations", center_equations)
        object.__setattr__(self, "_eq_no", eq_start)
        object.__setattr__(self, "_eq_labels", {})  # label -> number

        output = (output or "notebook").lower().strip()
        if output not in ("notebook", "asis"):
            raise ValueError("output must be 'notebook' or 'asis'")
        object.__setattr__(self, "_output", output)

    def __getattr__(self, name: str):
        try:
            return getattr(self._ureg, name)
        except UndefinedUnitError:
            raise AttributeError(name)
        except Exception:
            raise AttributeError(name)

    def reset_eq(self, n: int = 0):
        self._eq_no = n

    def next_eq(self, label: str | None = None) -> int:
        self._eq_no += 1
        if label:
            self._eq_labels[label] = self._eq_no
        return self._eq_no

    def eq(self, label: str) -> int:
        return self._eq_labels[label]

    # Quarto/PDF compatible renderer (NO HTML)
    def render_equation(self, latex: str, center: bool | None = None):
        if center is None:
            center = self._center_equations

        # Quarto/PDF: emit raw LaTeX only (requires chunk output: asis)
        if self._output == "asis":
            if center:
                print(f"$$\n{latex}\n$$\n")
            else:
                print("$$\n\\begin{aligned}\n& " + latex + "\n\\end{aligned}\n$$\n")
            return

        # Notebook: rich display
        if center:
            display(Math(latex))
        else:
            display(Math("\\begin{aligned} & " + latex + " \\end{aligned}"))

    def _make_engvar(self, rhs: Any) -> EngVar:
        if isinstance(rhs, EngVar):
            return rhs
        if isinstance(rhs, pint.Quantity):
            return EngVar(rhs)
        if isinstance(rhs, (tuple, list)):
            if len(rhs) == 0:
                raise ValueError("Empty tuple/list is not a valid variable definition.")
            value = rhs[0]
            units = rhs[1] if len(rhs) >= 2 else None
            desc = rhs[2] if len(rhs) >= 3 else ""
            if isinstance(value, pint.Quantity):
                q = value
            else:
                q = Q_(value, units) if units else Q_(value, self._ureg.dimensionless)
            return EngVar(q, desc=desc)
        if isinstance(rhs, (int, float)):
            return EngVar(Q_(rhs, self._ureg.dimensionless))
        raise TypeError(f"Unsupported assignment type: {type(rhs)}")

    def _show_assignment(self, name: str, var: EngVar, show: bool | None = None):
        if show is None:
            show = self._auto_display
        if not show:
            return
        if var.desc:
            desc = _escape_latex_text(var.desc)
            self.render_equation(rf"{name} = {var}\;\;\text{{({desc})}}", center=False)
        else:
            self.render_equation(rf"{name} = {var}", center=False)

    def __setattr__(self, name: str, value: Any):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        var = self._make_engvar(value)
        self._vars[name] = var
        object.__setattr__(self, name, var)
        self._show_assignment(name, var)

    def define(
        self,
        name: str,
        value: Any,
        units: str | None = None,
        comment: str = "",
        show: bool | None = None,
    ) -> EngVar:
        rhs = (value, units, comment) if units is not None or comment else (value, units)
        var = self._make_engvar(rhs)
        self._vars[name] = var
        object.__setattr__(self, name, var)
        self._show_assignment(name, var, show=show)
        return var

    def validate(
        self,
        expr: str | CalcExpr,
        required_vars: Dict[str, str] | list[str] | None = None,
        expected_units: str | None = None,
        overrides: Optional[Dict[str, pint.Quantity]] = None,
        raise_on_error: bool = False,
    ) -> ValidationReport:
        calc = expr if isinstance(expr, CalcExpr) else self.expr(expr)
        return calc.validate(
            required_vars=required_vars,
            expected_units=expected_units,
            overrides=overrides,
            raise_on_error=raise_on_error,
        )

    def __getitem__(self, name: str) -> EngVar:
        return self._vars[name]

    # silent expression builder (NO printing)
    def expr(self, s: str, out_units: str | None = None, fmt: str = "g", length_unit: str | None = None) -> CalcExpr:
        if "=" in s:
            lhs, rhs = s.split("=", 1)
            lhs, rhs = lhs.strip(), rhs.strip()
        else:
            lhs, rhs = "", s.strip()

        obj = CalcExpr(
            env=self,
            lhs=lhs,
            rhs=rhs,
            out_units=out_units,
            fmt=fmt,
            length_unit=length_unit,
            tag=None,
            store=False,
            overrides=None,
        )
        obj._number_default = self._eq_numbers
        obj._center_default = self._center_equations
        return obj

    def equation(self, s: str, out_units: str | None = None, fmt: str = "g", length_unit: str | None = None) -> CalcExpr:
        return self.expr(s=s, out_units=out_units, fmt=fmt, length_unit=length_unit)

    # show + return CalcExpr (prints once)
    def show_calcs(
        self,
        s: str,
        out_units: str | None = None,
        fmt: str = "g",
        length_unit: str | None = None,
        view: str = "full",
        tag: str | int | None = None,
        number: bool | None = None,
        center: bool | None = None,
        store: bool = True,
    ) -> CalcExpr:
        if "=" in s:
            lhs, rhs = s.split("=", 1)
            lhs, rhs = lhs.strip(), rhs.strip()
        else:
            lhs, rhs = "", s.strip()

        obj = CalcExpr(
            env=self,
            lhs=lhs,
            rhs=rhs,
            out_units=out_units,
            fmt=fmt,
            length_unit=length_unit,
            tag=tag,
            store=store,
            overrides=None,
        )
        obj._number_default = self._eq_numbers if number is None else bool(number)
        obj._center_default = self._center_equations if center is None else bool(center)

        obj.show_calcs(view=view, tag=tag, number=number, center=center, store=store)
        return obj
