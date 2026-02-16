"""
calcs.units
-----------
Single source of truth for units across your calc library.

Usage:
    from calcs.units import ureg, Q_
    P = Q_(120, "kip")
"""
from __future__ import annotations

import pint

# Create ONE registry for the whole library.
ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity

# --- Common US structural aliases (extend as you like) ---
# Force / stress
ureg.define("kip = 1000 * lbf = kip")
ureg.define("ksi = kip / inch**2 = ksi")

# Area / inertia convenience
ureg.define("in2 = inch**2 = in2")
ureg.define("in4 = inch**4 = in4")

# Distributed loads / weights
ureg.define("psf = lbf / foot**2 = psf")
ureg.define("pcf = lbf / foot**3 = pcf")

# Moment
ureg.define("kip_ft = kip * foot = kip_ft")
ureg.define("kip_in = kip * inch = kip_in")
