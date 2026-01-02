def get_char_value(c: str) -> int:
    if c.isdigit():
        return int(c)
    if "A" <= c <= "Z":
        return ord(c) - ord("A") + 10
    if c == "<":
        return 0
    return 0


def compute_check_digit(data: str) -> int:
    weights = [7, 3, 1]
    return sum(get_char_value(c) * weights[i % 3] for i, c in enumerate(data)) % 10


def clean_ocr_digit(char: str) -> str:
    return {
        "O": "0",
        "D": "0",
        "Q": "0",
        "S": "5",
        "B": "8",
        "Z": "2",
        "I": "1",
    }.get(char, char)
