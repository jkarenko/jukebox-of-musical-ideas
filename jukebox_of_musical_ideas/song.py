from pydantic import BaseModel
from typing import List, Optional

class Song(BaseModel):
    progression: List[str]
    tempo: Optional[int] = 120
    bars: Optional[int] = 1
    style: Optional[str] = "basic"
