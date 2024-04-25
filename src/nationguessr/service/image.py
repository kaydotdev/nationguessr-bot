import os
from textwrap import TextWrapper
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

FontRGBColor = Tuple[int, int, int]
TextXYPosition = Tuple[int, int]


class ImageEditService:
    def __init__(
        self,
        font_path: str | os.PathLike,
        font_color: FontRGBColor,
        pad: int = 5,
        max_width: int = 55,
    ):
        self._font_path = font_path
        self._font_color = font_color
        self._text_wrapper = TextWrapper(width=max_width)
        self._pad = pad

    def add_text(
        self,
        image: Image,
        text: str,
        text_size: int = 14,
        position: TextXYPosition = (0, 0),
        center: bool = False,
    ) -> Image:
        """

        Args:
            image:
            text:
            text_size:
            position:
            center:

        Returns:

        """

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self._font_path, text_size)

        _, _, text_width, text_height = draw.multiline_textbbox((0, 0), text, font=font)

        offset_x, offset_y = position

        x = (image.width - text_width) / 2 if center else 0
        y = (image.height - text_height) / 2 if center else 0

        draw.text((x + offset_x, y + offset_y), text, font=font, fill=self._font_color)

        return image

    def add_multiline_text(
        self,
        image: Image,
        text: List[str],
        text_size: int = 14,
        position: TextXYPosition = (0, 0),
        center: bool = False,
    ) -> Image:
        """

        Args:
            image:
            text:
            text_size:
            position:
            center:

        Returns:

        """

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self._font_path, text_size)

        multiline_text = [
            chunk for line in text for chunk in self._text_wrapper.wrap(text=line)
        ]
        concatenated_text = "\n".join(multiline_text)

        _, _, text_width, text_height = draw.multiline_textbbox(
            (0, 0), concatenated_text, font=font
        )

        max_width = max(draw.textlength(line, font=font) for line in multiline_text)
        offset_x, offset_y = position

        x = (image.width - max_width) / 2 if center else 0
        y = (image.height - text_height) / 2 if center else 0

        for line in multiline_text:
            _, _, line_width, line_height = draw.textbbox((0, 0), line, font=font)
            draw.text(
                (x + offset_x, y + offset_y), line, font=font, fill=self._font_color
            )
            y += line_height + self._pad

        return image
