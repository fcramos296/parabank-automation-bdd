EMPTY_VALUE = "[vazio]"


def normalize_example_value(value: str) -> str:
    """Translate explicit Gherkin sentinels into runtime values."""

    return "" if value == EMPTY_VALUE else value
