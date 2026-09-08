import ast
from datetime import datetime
import io
import math
import re
import sys
import time
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bin": bin,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "pow": pow,
    "print": print,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
}

ALLOWED_MODULES = {"math", "datetime", "pandas", "pd", "numpy", "np"}
BLOCKED_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
}


class CodeSandboxError(Exception):
    pass


class CodeSandbox:
    """Safely inspects and executes Python code on a Pandas DataFrame."""

    @staticmethod
    def extract_code(raw_text: str) -> str:
        """Extracts python code from raw LLM output or markdown blocks."""
        text = raw_text.strip()
        # Look for ```python ... ```
        pattern = r"```(?:python)?\s*([\s\S]*?)```"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
        return text

    @classmethod
    def validate_ast(cls, code_str: str) -> None:
        """Validates that code does not attempt restricted operations."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            raise CodeSandboxError(f"Syntax error in generated code: {e}") from e

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_base = alias.name.split(".")[0]
                        if mod_base not in ALLOWED_MODULES:
                            raise CodeSandboxError(
                                f"Restricted import '{alias.name}'. Only pandas, numpy, math, datetime are allowed."
                            )
                elif isinstance(node, ast.ImportFrom):
                    mod_base = (node.module or "").split(".")[0]
                    if mod_base not in ALLOWED_MODULES:
                        raise CodeSandboxError(
                            f"Restricted import from '{node.module}'. Only pandas, numpy, math, datetime are allowed."
                        )

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                    raise CodeSandboxError(
                        f"Blocked dangerous function call: '{node.func.id}()'"
                    )
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr.startswith("__")
                ):
                    raise CodeSandboxError(
                        f"Blocked dunder attribute call: '{node.func.attr}'"
                    )

    @classmethod
    def serialize_result(cls, val: Any) -> Dict[str, Any]:
        """Converts raw Python / Pandas outputs into JSON-serializable payloads."""
        if val is None:
            return {"type": "none", "value": None}

        if isinstance(val, (int, np.integer)):
            return {"type": "scalar", "value": int(val), "formatted": f"{int(val):,}"}

        if isinstance(val, (float, np.floating)):
            f_val = float(val)
            if math.isnan(f_val):
                return {"type": "scalar", "value": None, "formatted": "NaN"}
            return {"type": "scalar", "value": round(f_val, 4), "formatted": f"{f_val:,.2f}"}

        if isinstance(val, (str, bool)):
            return {"type": "scalar", "value": val, "formatted": str(val)}

        if isinstance(val, pd.DataFrame):
            df_display = val.head(100).copy()
            # Replace NaNs
            df_display = df_display.fillna("")
            return {
                "type": "dataframe",
                "total_rows": len(val),
                "columns": [str(c) for c in val.columns],
                "rows": df_display.to_dict(orient="records"),
                "shape": list(val.shape),
            }

        if isinstance(val, pd.Series):
            s_display = val.head(100).fillna("").to_dict()
            return {
                "type": "series",
                "name": str(val.name or "Series"),
                "total_items": len(val),
                "items": [{"key": str(k), "value": v} for k, v in s_display.items()],
            }

        if isinstance(val, (list, tuple)):
            clean_list = []
            for item in val[:50]:
                if isinstance(item, (int, np.integer)):
                    clean_list.append(int(item))
                elif isinstance(item, (float, np.floating)):
                    clean_list.append(round(float(item), 4))
                else:
                    clean_list.append(str(item))
            return {"type": "list", "items": clean_list, "total_items": len(val)}

        if isinstance(val, dict):
            clean_dict = {}
            for k, v in list(val.items())[:50]:
                if isinstance(v, (int, np.integer)):
                    clean_dict[str(k)] = int(v)
                elif isinstance(v, (float, np.floating)):
                    clean_dict[str(k)] = round(float(v), 4)
                elif isinstance(v, (list, tuple)):
                    clean_dict[str(k)] = [str(x) for x in v[:10]]
                else:
                    clean_dict[str(k)] = str(v)
            return {"type": "dict", "value": clean_dict}

        # Fallback to string representation
        return {"type": "scalar", "value": str(val), "formatted": str(val)}

    @classmethod
    def execute(cls, code_str: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Executes the given Python code in a safe sandbox environment."""
        clean_code = cls.extract_code(code_str)

        start_time = time.perf_counter()
        try:
            cls.validate_ast(clean_code)
        except CodeSandboxError as err:
            return {
                "success": False,
                "error": str(err),
                "code": clean_code,
                "execution_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "result": None,
                "stdout": "",
            }

        safe_globals = {
            "pd": pd,
            "np": np,
            "datetime": datetime,
            "math": math,
            "__builtins__": SAFE_BUILTINS,
        }
        local_scope = {"df": df.copy()}

        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        try:
            # Check if code is a single expression or statement list
            parsed = ast.parse(clean_code)
            result = None

            if len(parsed.body) == 1 and isinstance(parsed.body[0], ast.Expr):
                # Single expression: evaluate directly
                compiled = compile(parsed, filename="<lumyd_sandbox>", mode="eval")
                result = eval(compiled, safe_globals, local_scope)
            else:
                # If last node is an expression and no 'result' assignment exists, capture it
                last_node = parsed.body[-1]
                has_result_assign = any(
                    isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "result" for target in node.targets)
                    for node in parsed.body
                )

                if isinstance(last_node, ast.Expr) and not has_result_assign:
                    # Execute all but last statement
                    exec_body = ast.Module(body=parsed.body[:-1], type_ignores=[])
                    if exec_body.body:
                        compiled_body = compile(exec_body, filename="<lumyd_sandbox>", mode="exec")
                        exec(compiled_body, safe_globals, local_scope)
                    # Evaluate last expression
                    expr_to_eval = ast.Expression(body=last_node.value)
                    compiled_expr = compile(expr_to_eval, filename="<lumyd_sandbox>", mode="eval")
                    result = eval(compiled_expr, safe_globals, local_scope)
                else:
                    compiled = compile(clean_code, filename="<lumyd_sandbox>", mode="exec")
                    exec(compiled, safe_globals, local_scope)
                    result = local_scope.get("result")
                    if result is None:
                        for candidate in ["ans", "output", "res", "summary", "final"]:
                            if candidate in local_scope:
                                result = local_scope[candidate]
                                break

            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            serialized_result = cls.serialize_result(result)

            return {
                "success": True,
                "error": None,
                "code": clean_code,
                "result": serialized_result,
                "execution_time_ms": exec_time_ms,
                "stdout": stdout_capture.getvalue().strip(),
            }

        except Exception as e:
            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}",
                "code": clean_code,
                "execution_time_ms": exec_time_ms,
                "result": None,
                "stdout": stdout_capture.getvalue().strip(),
            }
        finally:
            sys.stdout = old_stdout
