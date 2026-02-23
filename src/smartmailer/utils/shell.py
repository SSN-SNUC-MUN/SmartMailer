PINK = "\033[95m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END_FORMATTING = "\033[0m"

def get_style(color: str) -> str:
    lookup = {
        "red": RED,
        "green": GREEN,
        "yellow": YELLOW,
        "blue": BLUE,
        "cyan": CYAN,
        "pink": PINK,
        "bold": BOLD,
        "underline": UNDERLINE,
        "end": END_FORMATTING,
    }
    return lookup.get(color, "")
