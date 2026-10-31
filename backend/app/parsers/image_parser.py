"""Decode and preprocess an uploaded screenshot with Pillow."""
import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

from ..schemas.roast import ParsedInput
from .web_parser import ParseError

MAX_SIDE = 1024


def parse_image(content: str) -> ParsedInput:
    b64 = content.split(",", 1)[1] if content.startswith("data:") else content
    try:
        raw = base64.b64decode(b64, validate=False)
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (binascii.Error, UnidentifiedImageError, OSError) as exc:
        raise ParseError("That doesn't look like a valid PNG/JPG/WebP image.") from exc

    img = img.convert("RGB")
    orig_size = img.size
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return ParsedInput(
        source="image",
        title="Screenshot",
        text=f"A UI screenshot/mockup of size {orig_size[0]}x{orig_size[1]}.",
        image_b64=base64.b64encode(buf.getvalue()).decode(),
        meta={"size": f"{orig_size[0]}x{orig_size[1]}"},
    )
