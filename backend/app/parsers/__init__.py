"""Parser registry. To add a parser, write a function and register it here."""
from ..schemas.roast import ParsedInput, RoastRequest
from .github_parser import parse_github
from .image_parser import parse_image
from .text_parser import parse_text
from .web_parser import ParseError, parse_url

__all__ = ["ParseError", "parse_input"]


async def parse_input(req: RoastRequest) -> ParsedInput:
    if req.input_type == "idea":
        return parse_text(req.content)
    if req.input_type == "github":
        return await parse_github(req.content)
    if req.input_type == "url":
        return await parse_url(req.content)
    if req.input_type == "image":
        return parse_image(req.content)
    raise ParseError(f"Unknown input type: {req.input_type}")
