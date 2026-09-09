import re
from typing import List, Dict, Any, Tuple, Optional
from src.ocr.schemas import BlockType

class DocumentClassifier:
    """Classifies raw text blocks into semantic document roles (Title, Heading, Paragraph, Header, Footer)."""

    def __init__(self):
        self.median_font_size = 10.0
        self.max_font_size = 14.0

    def perform_first_pass(self, pages_raw_blocks: List[List[Dict[str, Any]]]):
        """Analyzes all blocks across pages to determine typical body font size."""
        all_sizes = []
        for page_blocks in pages_raw_blocks:
            for b in page_blocks:
                size = b.get("font_size", 10.0)
                if size > 0:
                    all_sizes.append(size)

        if all_sizes:
            all_sizes.sort()
            self.median_font_size = all_sizes[len(all_sizes) // 2]
            self.max_font_size = max(all_sizes)
        else:
            self.median_font_size = 10.0
            self.max_font_size = 14.0

    def classify_block(
        self,
        rb: Dict[str, Any],
        prev_rb: Optional[Dict[str, Any]],
        next_rb: Optional[Dict[str, Any]],
        page_height: float
    ) -> Tuple[BlockType, float, str]:
        """
        Classifies a block into BlockType, with confidence and reasoning.
        """
        text = rb.get("text", "").strip()
        font_size = rb.get("font_size", self.median_font_size)
        bbox = rb.get("bbox", (0, 0, 0, 0))
        y0, y1 = bbox[1], bbox[3]

        if not text:
            return BlockType.UNKNOWN, 0.5, "Empty block text"

        # Check for header (top 8% of page)
        if y1 < page_height * 0.08 and len(text) < 120:
            return BlockType.HEADER, 0.88, "Positioned at top margin"

        # Check for footer (bottom 8% of page)
        if y0 > page_height * 0.92 and len(text) < 100:
            return BlockType.FOOTER, 0.90, "Positioned at bottom margin"

        # Check for title (significantly larger than median, near top)
        if font_size >= self.median_font_size * 1.5 and y0 < page_height * 0.35:
            return BlockType.TITLE, 0.92, f"Large font ({font_size:.1f}pt) near page top"

        # Check for section heading (larger than median or numbered pattern like '1. ', '12. ')
        is_numbered_section = bool(re.match(r'^\d+(\.\d+)*\s+[A-Z]', text))
        if font_size >= self.median_font_size * 1.2 or (is_numbered_section and len(text) < 120):
            return BlockType.HEADING, 0.85, f"Prominent font or numbered header pattern"

        # Check for bullet or list item
        if re.match(r'^(\*|-|•|\d+\.)\s+', text):
            return BlockType.LIST_ITEM, 0.85, "Starts with bullet or list marker"

        # Default: paragraph body text
        return BlockType.PARAGRAPH, 0.95, "Standard body text block"

    def assign_heading_levels(self, flat_dicts: List[Dict[str, Any]]):
        """Assigns heading_level (1, 2, 3) based on relative font size among headings."""
        heading_sizes = set()
        for d in flat_dicts:
            if d.get("block_type") in (BlockType.TITLE, BlockType.HEADING):
                heading_sizes.add(d.get("font_size", 12.0))

        sorted_sizes = sorted(heading_sizes, reverse=True)
        size_to_level = {size: idx + 1 for idx, size in enumerate(sorted_sizes[:3])}

        for d in flat_dicts:
            if d.get("block_type") in (BlockType.TITLE, BlockType.HEADING):
                size = d.get("font_size", 12.0)
                d["heading_level"] = size_to_level.get(size, 2)
            else:
                d["heading_level"] = None
