from IPython.display import display, Math

def show_eq(tex: str):
    """Display a LaTeX equation string (no $$ needed)."""
    display(Math(tex))

def show_value(name_tex: str, q, unit: str, fmt="{:.3f}"):
    """Show a pint quantity converted to unit."""
    q2 = q.to(unit)
    display(Math(rf"{name_tex} = {fmt.format(q2.magnitude)}\ \mathrm{{{unit}}}"))
    return q2
