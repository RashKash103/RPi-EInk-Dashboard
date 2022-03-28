from PIL import ImageFont
from enum import Enum

class Style(Enum):
    REGULAR = "regular"
    BOLD = "bold"
    LIGHT = "light"

font_reg = ImageFont.truetype("fonts/RobotoSlab-Regular.ttf")
font_bold = ImageFont.truetype("fonts/RobotoSlab-Bold.ttf")
font_light = ImageFont.truetype("fonts/RobotoSlab-Light.ttf")

def get_font(style: Style, size: int) -> ImageFont:
    if style == Style.REGULAR:
        return font_reg.font_variant(size = size)
    elif style == Style.BOLD:
        return font_bold.font_variant(size = size)
    elif style == Style.LIGHT:
        return font_light.font_variant(size = size)
