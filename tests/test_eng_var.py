import unittest

from re_lib.eng_var import EngEnv


class TestEngVarWorkflow(unittest.TestCase):
    def test_symbolic_first_then_numeric(self):
        env = EngEnv(auto_display=False)
        expr = env.equation("M_n = F_y * Z_x")

        # Should render symbolically without requiring variables yet.
        expr.show_calcs(view="sym")

        env.define("F_y", 50, "ksi", show=False)
        env.define("Z_x", 100, "in^3", show=False)

        result = expr.show_calcs(view="num", out_units="kip*in")
        self.assertAlmostEqual(result.to("kip*in").magnitude, 5000.0, places=6)

    def test_variable_metadata_updates(self):
        env = EngEnv(auto_display=False)
        z = env.define("Z_x", 100, "in^3", comment="initial", show=False)

        z.units = "ft^3"
        z.comment = "updated"

        self.assertEqual(z.comment, "updated")
        self.assertEqual(str(z.quantity.units), "foot ** 3")

    def test_validator_missing_variables(self):
        env = EngEnv(auto_display=False)
        report = env.validate("M_n = F_y * Z_x")

        self.assertFalse(report.valid)
        self.assertEqual(report.missing_vars, ["F_y", "Z_x"])

    def test_validator_unit_checks(self):
        env = EngEnv(auto_display=False)
        env.define("F_y", 50, "ksi", show=False)
        env.define("Z_x", 100, "in^3", show=False)

        good = env.validate(
            "M_n = F_y * Z_x",
            required_vars={"F_y": "ksi", "Z_x": "in^3"},
            expected_units="kip*in",
        )
        self.assertTrue(good.valid)

        bad = env.validate(
            "M_n = F_y * Z_x",
            required_vars={"F_y": "in"},
        )
        self.assertFalse(bad.valid)
        self.assertTrue(any("Variable 'F_y'" in msg for msg in bad.unit_errors))


if __name__ == "__main__":
    unittest.main()
