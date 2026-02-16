# re_lib/aci/concrete_section.py
from __future__ import annotations

from re_lib.eng_var import CalcExpr


def setup_concrete_section(v, *, fc_ksi: float = 4.0, Ac_in2: float = 200.0):
    v.f_c = (fc_ksi, "ksi", "Concrete compressive strength")
    v.A_c = (Ac_in2, "in^2", "Concrete area")


def calc_PD(v, *, number=None, center=None, tag=None):
    return v.show_calcs(
        "P_D=(0.85*f_c*A_c)/2",
        out_units="kip",
        fmt=".2f",
        number=number,
        center=center,
        tag=tag,
    )


def expr_PD(v):
    """
    Silent expression builder WITHOUT requiring v.expr(...).
    """
    obj = CalcExpr(
        env=v,
        lhs="P_D",
        rhs="(0.85*f_c*A_c)/2",
        out_units="kip",
        fmt=".2f",
        length_unit=None,
        tag=None,
        store=False,
        overrides=None,
    )
    # inherit env defaults
    obj._number_default = getattr(v, "_eq_numbers", False)
    obj._center_default = getattr(v, "_center_equations", True)
    return obj

# re_lib/aci/moment_check.py
# ACI 318-19 flexural strength check for a *singly-reinforced rectangular* section
# Units: use EngEnv (pint). Typical: fc, fy in ksi; b, d in in; As in in^2; Mu in kip*ft or kip*in.


from dataclasses import dataclass
from typing import Optional, Dict, Any

import pint

# If you use your EngEnv/CalcExpr engine:
from re_lib.eng_var import EngEnv, EngVar


@dataclass
class MomentCheckResult:
    ok: bool
    phi: float
    eps_t: float
    a: pint.Quantity
    c: pint.Quantity
    Mn: pint.Quantity
    phiMn: pint.Quantity
    Mu: pint.Quantity
    ratio: float  # Mu/(phiMn)


def beta1_aci318_19(fc: pint.Quantity) -> float:
    """
    ACI 318-19 rectangular stress block beta1:
      beta1 = 0.85 for fc' <= 4 ksi
      reduces by 0.05 per 1 ksi above 4 ksi to min 0.65
    """
    fc_ksi = fc.to("ksi").magnitude
    if fc_ksi <= 4.0:
        return 0.85
    b1 = 0.85 - 0.05 * (fc_ksi - 4.0)
    return max(0.65, float(b1))


def phi_flexure_aci318_19(eps_t: float, reinforcement: str = "tied") -> float:
    """
    ACI 318-19 phi for flexure based on tensile strain at nominal strength.
    Common implementation:
      tension-controlled (eps_t >= 0.005): phi = 0.90
      compression-controlled (eps_t <= 0.002): phi = 0.65 (tied), 0.75 (spiral)
      transition: linear between 0.002 and 0.005
    """
    reinforcement = reinforcement.lower().strip()
    phi_cc = 0.75 if reinforcement == "spiral" else 0.65

    if eps_t >= 0.005:
        return 0.90
    if eps_t <= 0.002:
        return phi_cc

    # linear interpolation
    return phi_cc + (0.90 - phi_cc) * (eps_t - 0.002) / (0.005 - 0.002)


def moment_check_rect_singly(
    v: EngEnv,
    *,
    Mu,                 # pint Quantity (e.g., 250*v.kip*v.ft)
    b, d, As, fc, fy,   # pint Quantities
    reinforcement: str = "tied",
    show: bool = True,
    number: bool | None = None,
    tag: str | int | None = None,
    center: bool | None = None,
) -> MomentCheckResult:
    """
    Flexural check for singly reinforced rectangular section:
      a  = As*fy / (0.85*fc*b)
      beta1 from ACI
      c  = a/beta1
      eps_t = 0.003*(d-c)/c
      Mn = As*fy*(d - a/2)
      phi = function(eps_t)
      check Mu <= phi*Mn

    Returns MomentCheckResult.
    """

    # Normalize moment units to kip*in internally
    Mu_q = Mu.to("kip*ft").to("kip*in") if Mu.check("[force] * [length]") else Mu

    # beta1, a, c
    b1 = beta1_aci318_19(fc)
    a = (As * fy / (0.85 * fc * b)).to("in")
    c = (a / b1).to("in")

    # strain at tensile steel at nominal strength
    eps_t = float((0.003 * (d - c) / c).to("dimensionless").magnitude)

    # nominal moment strength
    Mn = (As * fy * (d - a / 2)).to("kip*in")

    # strength reduction factor
    phi = phi_flexure_aci318_19(eps_t, reinforcement=reinforcement)
    phiMn = (phi * Mn).to("kip*in")

    ratio = float((Mu_q / phiMn).to("dimensionless").magnitude)
    ok = ratio <= 1.0

    if show:
        # Put inputs into env for nice printing
        v.M_u = EngVar(Mu_q, "Factored moment demand")
        v.b = EngVar(b, "Section width")
        v.d = EngVar(d, "Effective depth")
        v.A_s = EngVar(As, "Tension steel area")
        v.f_c = EngVar(fc, "Concrete compressive strength")
        v.f_y = EngVar(fy, "Steel yield strength")

        # Show beta1 as plain text/math (dimensionless)
        v.render_equation(rf"\beta_1 = {b1:.2f}", center=center)

        # Show calcs (use your engine)
        v.show_calcs("a=(A_s*f_y)/(0.85*f_c*b)", out_units="in", fmt=".3f", number=number, tag=tag, center=center)
        v.render_equation(rf"c = \frac{{a}}{{\beta_1}} = {_fmt_qty(c, '.3f')}", center=center)

        v.render_equation(
            rf"\varepsilon_t = 0.003\frac{{d-c}}{{c}} = {eps_t:.4f}",
            center=center
        )

        v.show_calcs("M_n=A_s*f_y*(d-a/2)", out_units="kip*in", fmt=".2f", number=number, tag="auto" if tag == "auto" else None, center=center)

        v.render_equation(rf"\phi = {phi:.2f}", center=center)
        v.render_equation(rf"\phi M_n = {phi:.2f}\,M_n = {_fmt_qty(phiMn, '.2f')}", center=center)

        v.render_equation(
            rf"\text{{Check: }} M_u \le \phi M_n \;\Rightarrow\; {_fmt_qty(Mu_q, '.2f')} \le {_fmt_qty(phiMn, '.2f')}"
            rf"\;\;\text{{({ 'OK' if ok else 'NG'})}}",
            center=center
        )

    return MomentCheckResult(
        ok=ok, phi=phi, eps_t=eps_t, a=a, c=c, Mn=Mn, phiMn=phiMn, Mu=Mu_q, ratio=ratio
    )


def _fmt_qty(q: pint.Quantity, fmt: str = ".2f") -> str:
    """Local helper for printing quantities in LaTeX using EngVar formatter."""
    return EngVar(q).latex(fmt=fmt)
