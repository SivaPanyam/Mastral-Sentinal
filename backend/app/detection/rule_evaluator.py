import re
import operator

def evaluate_condition(condition: dict, field_value: str) -> bool:
    """
    Evaluates a single condition against a field value.
    Supported operators: ==, !=, >, <, >=, <=, contains, in, regex
    """
    if condition is None:
        return True
        
    op = condition.get("operator", "==")
    target_value = condition.get("value")

    if field_value is None:
        return False

    # String operations
    if op == "==":
        return str(field_value) == str(target_value)
    elif op == "!=":
        return str(field_value) != str(target_value)
    elif op == "contains":
        return str(target_value).lower() in str(field_value).lower()
    elif op == "in":
        if isinstance(target_value, list):
            return field_value in target_value
        return field_value in str(target_value)
    elif op == "regex":
        try:
            return bool(re.search(str(target_value), str(field_value)))
        except re.error:
            return False

    # Numeric operations (try to cast)
    try:
        num_val = float(field_value)
        num_target = float(target_value)
        if op == ">": return num_val > num_target
        if op == "<": return num_val < num_target
        if op == ">=": return num_val >= num_target
        if op == "<=": return num_val <= num_target
    except (ValueError, TypeError):
        pass

    return False
