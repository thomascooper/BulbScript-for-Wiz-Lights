from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class LightPattern:
    name: str
    colors: List[Tuple[int, int, int]]
    interval: float

PATTERNS = {
    "80s_christmas": LightPattern(
        name="80's Christmas Lights",
        colors=[
            (0, 255, 0),    # Green
            (255, 0, 0),    # Red
            (0, 0, 255),    # Blue
            (255, 30, 0),   # Orange
            (255, 10, 30),  # Pink
            (0, 255, 0),    # Green
            (255, 0, 0),    # Red
            (0, 0, 255),    # Blue
            (255, 30, 0),   # Orange
            (255, 10, 30),  # Pink
        ],
        interval=1.5
    )
} 