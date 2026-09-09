from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple

def preprocess_image_for_ocr(image_path: str) -> str:
    """
    Preprocesses any image format to maximize OCR character recognition:
    - Converts RGBA / Palette / Grayscale to clean RGB
    - Auto-scales resolution if image is too small or too large
    - Light contrast adjustment for sharp character edges
    """
    img = Image.open(image_path)
    
    # 1. Ensure RGB mode
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    w, h = img.size
    
    # 2. Scale small images to ensure character heights are legible (> 30px)
    if w < 600 or h < 600:
        scale_factor = max(600 / max(w, 1), 600 / max(h, 1))
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)
    elif w > 3200 or h > 3200:
        # Scale down extremely large images to save memory
        scale_factor = min(3200 / w, 3200 / h)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 3. Moderate contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    
    # Save back to disk preserving matching format
    ext = Path(image_path).suffix.lower()
    fmt = "JPEG" if ext in [".jpg", ".jpeg"] else ("WEBP" if ext == ".webp" else "PNG")
    if fmt == "JPEG":
        img.save(image_path, format="JPEG", quality=95)
    else:
        img.save(image_path, format=fmt)
    return image_path

