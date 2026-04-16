"""Navigation signal exceptions for CompliGator's interactive CLI."""


class BackSignal(Exception):
    """User pressed 'b' — go back one level."""


class ExitToMainSignal(Exception):
    """User pressed 'x' — return to main menu."""


class QuitSignal(Exception):
    """User pressed 'q' — exit the application."""


def prompt(text: str) -> str:
    """Read input and raise navigation signals on b / x / q."""
    val = input(text).strip().lower()
    if val == "b":
        raise BackSignal
    if val == "x":
        raise ExitToMainSignal
    if val == "q":
        raise QuitSignal
    return val
