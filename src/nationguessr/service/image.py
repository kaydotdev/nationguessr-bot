from textwrap import TextWrapper
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

FontRGBColor = Tuple[int, int, int]
TextXYPosition = Tuple[int, int]


class ImageEditService:
    def __init__(
        self,
        font: ImageFont,
        font_color: FontRGBColor,
        pad: int = 5,
        max_width: int = 55,
    ):
        self._font = font
        self._font_color = font_color
        self._text_wrapper = TextWrapper(width=max_width)
        self._pad = pad

    def add_text(
        self,
        image: Image,
        text: str,
        position: TextXYPosition = (0, 0),
        center: bool = False,
    ) -> Image:
        """

        Args:
            image:
            text:
            position:
            center:

        Returns:

        """

        draw = ImageDraw.Draw(image)

        _, _, text_width, text_height = draw.multiline_textbbox(
            (0, 0), text, font=self._font
        )

        offset_x, offset_y = position

        x = (image.width - text_width) / 2 if center else 0
        y = (image.height - text_height) / 2 if center else 0

        draw.text(
            (x + offset_x, y + offset_y), text, font=self._font, fill=self._font_color
        )

        return image

    def add_multiline_text(
        self,
        image: Image,
        text: List[str],
        position: TextXYPosition = (0, 0),
        center: bool = False,
    ) -> Image:
        """

        Args:
            image:
            text:
            position:
            center:

        Returns:

        """

        draw = ImageDraw.Draw(image)

        multiline_text = [
            chunk for line in text for chunk in self._text_wrapper.wrap(text=line)
        ]
        concatenated_text = "\n".join(multiline_text)

        _, _, text_width, text_height = draw.multiline_textbbox(
            (0, 0), concatenated_text, font=self._font
        )

        max_width = max(
            draw.textlength(line, font=self._font) for line in multiline_text
        )
        offset_x, offset_y = position

        x = (image.width - max_width) / 2 if center else 0
        y = (image.height - text_height) / 2 if center else 0

        for line in multiline_text:
            _, _, line_width, line_height = draw.textbbox((0, 0), line, font=self._font)
            draw.text(
                (x + offset_x, y + offset_y),
                line,
                font=self._font,
                fill=self._font_color,
            )
            y += line_height + self._pad

        return image
