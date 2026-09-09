from typing import Optional, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field

class BlockType(str, Enum):
    TITLE = "TITLE"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    LIST_ITEM = "LIST_ITEM"
    TABLE = "TABLE"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    UNKNOWN = "UNKNOWN"

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class BlockSchema(BaseModel):
    block_id: str
    page_number: int
    reading_order: int
    block_type: BlockType = BlockType.PARAGRAPH
    text: str
    bounding_box: BoundingBox
    font_size: float = 12.0
    font_family: str = "OCR-Tesseract"
    bold: bool = False
    italic: bool = False
    confidence: float = 1.0
    provenance: str = "OCR"
    heading_level: Optional[int] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
