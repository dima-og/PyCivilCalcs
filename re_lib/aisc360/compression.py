import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import pint

def slenderness_ratio(K: float, L: pint.Quantity, r: pint.Quantity) -> float:
    KLr = (K * L / r).to_reduced_units()
    return float(KLr.magnitude)

def euler_fe(E: pint.Quantity, KLr: float, stress_units: str) -> pint.Quantity:
    return (math.pi**2 * E / (KLr**2)).to(stress_units)

def lambda_c(Fy: pint.Quantity, Fe: pint.Quantity) -> float:
    return math.sqrt(float((Fy / Fe).to_reduced_units().magnitude))

def e3_fcr(Fy, E, K, L, r):
    stress_units = f"{Fy.units:~}"
    KLr = slenderness_ratio(K, L, r)
    Fe = euler_fe(E.to(stress_units), KLr, stress_units)
    lam = lambda_c(Fy.to(stress_units), Fe)
    if lam <= 1.5:
        Fcr = (0.658 ** (lam**2)) * Fy
        branch = "inelastic"
    else:
        Fcr = 0.877 * Fe
        branch = "elastic"
    return Fcr.to(stress_units), Fe.to(stress_units), lam, KLr, branch

def e3_pn(Fcr, Ag, force_units="kip"):
    return (Fcr * Ag).to(force_units)

@dataclass(frozen=True)
class E3AxisResult:
    axis: str
    K: float
    L: pint.Quantity
    r: pint.Quantity
    KLr: float
    Fe: pint.Quantity
    lambda_c: float
    branch: str
    Fcr: pint.Quantity
    Pn: pint.Quantity

def e3_per_axis(Fy, E, Ag, axes: Iterable[Dict], force_units="kip") -> List[E3AxisResult]:
    out = []
    for a in axes:
        axis = str(a.get("axis", ""))
        K = float(a["K"])
        L = a["L"]
        r = a["r"]
        Fcr, Fe, lam, KLr, branch = e3_fcr(Fy, E, K, L, r)
        Pn = e3_pn(Fcr, Ag, force_units=force_units)
        out.append(E3AxisResult(axis, K, L, r, KLr, Fe, lam, branch, Fcr, Pn))
    return out

def e3_controlling_axis(results: Iterable[E3AxisResult]) -> E3AxisResult:
    results = list(results)
    return min(results, key=lambda r: float(r.Pn.to("kip").magnitude))

def e3_summary_dict(results: Iterable[E3AxisResult]) -> List[Dict]:
    out = []
    for r in results:
        out.append({
            "Axis": r.axis,
            "K": r.K,
            "L": f"{r.L:~P}",
            "r": f"{r.r:~P}",
            "KL/r": r.KLr,
            "Fe": f"{r.Fe:~P}",
            "λc": r.lambda_c,
            "Branch": r.branch,
            "Fcr": f"{r.Fcr:~P}",
            "Pn": f"{r.Pn:~P}",
        })
    return out
