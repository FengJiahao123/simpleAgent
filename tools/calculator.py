import math
from tools.base import Tool


class Calculator(Tool):
    name = "calculator"
    description = "Safely evaluate a mathematical expression. Supports +, -, *, /, **, sqrt(), abs(), and parentheses."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate, e.g. '(3 + 4) * 2' or 'sqrt(144)'."
            }
        },
        "required": ["expression"]
    }

    _ALLOWED_NAMES = {
        "sqrt": math.sqrt,
        "abs": abs,
        "pow": pow,
        "round": round,
        "min": min,
        "max": max,
        "pi": math.pi,
        "e": math.e,
    }

    def execute(self, expression: str, **kwargs) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, self._ALLOWED_NAMES)
            if isinstance(result, float):
                return str(round(result, 4))
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {e}"
