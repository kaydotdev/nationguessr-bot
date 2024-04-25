import io
import os
from typing import List

from aiogram.types import BufferedInputFile
from PIL import Image

from ..service.image import ImageEditService
from ..settings import Settings


def edit_game_over_card(
    image_edit_service: ImageEditService,
    app_settings: Settings,
    final_score: int,
) -> BufferedInputFile:
    game_over_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_over.png"
    )

    with (
        Image.open(game_over_card_template_path) as game_over_card_template,
        io.BytesIO() as img_buffer,
    ):
        game_over_card_image = image_edit_service.add_text(
            game_over_card_template,
            str(final_score),
            text_size=128,
            position=(0, 10),
            center=True,
        )
        game_over_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)
        img_bytes = img_buffer.read()

    return BufferedInputFile(img_bytes, filename="game_over_card.png")


def edit_quiz_game_card(
    image_edit_service: ImageEditService,
    app_settings: Settings,
    round_facts: List[str],
) -> BufferedInputFile:
    quiz_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_guessing.png"
    )

    with (
        Image.open(quiz_card_template_path) as quiz_card_template,
        io.BytesIO() as img_buffer,
    ):
        numerated_text = [f"{i + 1}. {chunk}" for i, chunk in enumerate(round_facts)]
        quiz_card_image = image_edit_service.add_multiline_text(
            quiz_card_template,
            numerated_text,
            text_size=28,
            position=(0, -100),
            center=True,
        )
        quiz_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)
        img_bytes = img_buffer.read()

    return BufferedInputFile(img_bytes, filename="quiz_card.png")
