from __future__ import annotations


def make_graph(percent: float, bar_length: int = 25, blocks: str = "░█") -> str:
    """Generate an ASCII bar chart string for a given percentage.

    Args:
        percent: Value between 0 and 100.
        bar_length: Total number of characters in the bar.
        blocks: Characters to use for empty and filled portions.
            Common options: "░█", "░▒▓█", "⣀⣄⣤⣦⣶⣷⣿"

    Returns:
        A string of length bar_length representing the bar.
    """
    if len(blocks) < 2:
        blocks = "░█"

    empty_char = blocks[0]
    full_char = blocks[-1]

    if len(blocks) == 2:
        filled = round(bar_length * percent / 100)
        filled = max(0, min(bar_length, filled))
        return full_char * filled + empty_char * (bar_length - filled)

    # Multi-block mode: use intermediate characters for partial fills
    num_levels = len(blocks) - 1  # number of fill levels (excluding empty)
    total_units = bar_length * num_levels
    filled_units = round(total_units * percent / 100)
    filled_units = max(0, min(total_units, filled_units))

    full_blocks = filled_units // num_levels
    remainder = filled_units % num_levels

    bar = full_char * full_blocks
    if remainder > 0 and full_blocks < bar_length:
        bar += blocks[remainder]
        bar += empty_char * (bar_length - full_blocks - 1)
    else:
        bar += empty_char * (bar_length - full_blocks)

    return bar
