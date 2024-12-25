from pydantic import BaseModel
from typing import List, Optional

class ChordProgression(BaseModel):
    key: str
    progression: List[str]
    tempo: int
    bars: Optional[int] = 1
    style: Optional[str] = "basic"
