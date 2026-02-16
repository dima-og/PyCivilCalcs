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

    def test_value_magnitude(self):
        env = EngEnv(auto_display=False)
        env.eq.M_n = "F_y * Z_x"
        env.F_y = (50, "ksi")
        env.Z_x = (100, "in^3")

        val = env.eq.M_n.value("kip*in")
        self.assertAlmostEqual(val, 5000.0, places=6)


if __name__ == "__main__":
    unittest.main()
