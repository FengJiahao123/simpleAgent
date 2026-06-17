import pytest
from tools.calculator import Calculator


class TestCalculator:
    @pytest.fixture
    def calc(self):
        return Calculator()

    def test_basic_arithmetic(self, calc):
        assert "7" in calc.execute(expression="3 + 4")
        assert "12" in calc.execute(expression="3 * 4")
        assert "2.0" in calc.execute(expression="10 / 5")
        assert "3" in calc.execute(expression="10 - 7")

    def test_complex_expression(self, calc):
        result = calc.execute(expression="(3 + 4) * 2 - 5")
        assert "9" in result

    def test_float_result(self, calc):
        result = calc.execute(expression="10 / 3")
        assert "3.3333" in result

    def test_square_root(self, calc):
        result = calc.execute(expression="sqrt(16)")
        assert "4" in result

    def test_power(self, calc):
        result = calc.execute(expression="2 ** 10")
        assert "1024" in result

    def test_rejects_dangerous_input(self, calc):
        """Calculator should reject attempts to access builtins or execute code."""
        result = calc.execute(expression="__import__('os').system('ls')")
        assert "error" in result.lower() or "invalid" in result.lower()
