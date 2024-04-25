import io
import os
from typing import List

from aiogram.types import BufferedInputFile
from PIL import Image

from ..data.game import GameSession
from ..service.game import number_as_character
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
    game_session: GameSession,
    app_settings: Settings,
    round_facts: List[str],
) -> BufferedInputFile:
    quiz_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_guessing.png"
    )

    heart_icon_path = os.path.join(app_settings.assets_folder, "icons", "heart.png")

    with (
        Image.open(quiz_card_template_path) as quiz_card_template,
        Image.open(heart_icon_path) as heart_icon,
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
        quiz_card_image = image_edit_service.add_text(
            quiz_card_image,
            number_as_character(game_session.current_score),
            text_size=64,
            position=(713, 50),
        )

        for i in range(game_session.lives_remained):
            quiz_card_template.paste(
                heart_icon, (100 + i * heart_icon.width, 50), mask=heart_icon
            )

        quiz_card_image.save(img_buffer, format="PNG")

        img_buffer.seek(0)
        img_bytes = img_buffer.read()

    return BufferedInputFile(img_bytes, filename="quiz_card.png")
