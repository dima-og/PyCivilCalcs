import unittest

from re_lib.eng_var import EngEnv


class TestEngVarWorkflow(unittest.TestCase):
    def test_equation_namespace(self):
        env = EngEnv(auto_display=False)
        env.eq.M_n = "F_y * Z_x"
        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        result = env.eq.M_n.show(out_units="kip*in")
        self.assertAlmostEqual(result.to("kip*in").magnitude, 5000.0, places=6)

    def test_show_default_mode(self):
        env = EngEnv(auto_display=False)
        expr = env.equation("M_n = F_y * Z_x")

        # No vars -> symbolic default; should not raise.
        self.assertIsNone(expr.show())

        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        # All vars defined -> numeric default.
        result = expr.show(out_units="kip*in")
        self.assertAlmostEqual(result.to("kip*in").magnitude, 5000.0, places=6)

    def test_variable_definition_variants_and_show(self):
        env = EngEnv(auto_display=False)

        env.F_t = 20
        self.assertEqual(env.F_t.quantity.magnitude, 20)

        env.F_t = (20, "ksi")
        self.assertEqual(str(env.F_t.quantity.units), "kip_per_square_inch")

        env.F_t = (20, "ksi", "Rupture modulus", True)
        self.assertEqual(env.F_t.comment, "Rupture modulus")

        # Explicit variable display API requested.
        env.F_t.show()

    def test_center_and_number_options(self):
        env = EngEnv(auto_display=False, eq_numbers=True, center_equations=False)
        env.eq.M_n = "F_y * Z_x"
        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        q = env.eq.M_n.show(number=True, center=False, out_units="kip*in")
        self.assertAlmostEqual(q.to("kip*in").magnitude, 5000.0, places=6)

    def test_notebook_centering_uses_html_wrapper(self):
        import re_lib.eng_var as eng_var

        env = EngEnv(auto_display=False, output="notebook", notebook_render_mode="html")
        captured = []

        orig_display = eng_var.display
        try:
            eng_var.display = lambda obj: captured.append(obj)
            env.render_equation("x = y", center=True)
            env.render_equation("x = y", center=False)
        finally:
            eng_var.display = orig_display

        self.assertIn("text-align:center", getattr(captured[0], "data", str(captured[0])))
        self.assertIn("text-align:left", getattr(captured[1], "data", str(captured[1])))

    def test_notebook_latex_mode_uses_math(self):
        import re_lib.eng_var as eng_var

        env = EngEnv(auto_display=False, output="notebook", notebook_render_mode="latex")
        captured = []

        orig_display = eng_var.display
        try:
            eng_var.display = lambda obj: captured.append(obj)
            env.render_equation("x = y", center=True)
            env.render_equation("x = y", center=False)
        finally:
            eng_var.display = orig_display

        self.assertIn("IPython.core.display.Math", str(type(captured[0])))
        self.assertIn("IPython.core.display.Math", str(type(captured[1])))

    def test_asis_centering_uses_gathered(self):
        import io
        from contextlib import redirect_stdout

        env = EngEnv(auto_display=False, output="asis")
        env.eq.M_n = "F_y * Z_x"
        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        buf = io.StringIO()
        with redirect_stdout(buf):
            env.eq.M_n.show(view="sym", center=True)
        txt = buf.getvalue()
        self.assertIn("\\begin{gathered}", txt)

    def test_value_magnitude(self):
        env = EngEnv(auto_display=False)
        env.eq.M_n = "F_y * Z_x"
        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        val = env.eq.M_n.value("kip*in")
        self.assertAlmostEqual(val, 5000.0, places=6)


if __name__ == "__main__":
    unittest.main()
