import io
import os
from typing import List

import aiofiles
from aiogram.types import BufferedInputFile
from PIL import Image

from ..data.game import GameSession
from ..service.game import number_as_character
from ..service.image import ImageEditService
from ..settings import Settings


async def edit_game_over_card(
    image_edit_service: ImageEditService,
    app_settings: Settings,
    final_score: int,
) -> BufferedInputFile:
    game_over_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_over.png"
    )

    async with aiofiles.open(game_over_card_template_path, "rb") as template_file:
        template_image_bytes = await template_file.read()

        with (
            io.BytesIO(template_image_bytes) as img_buffer,
            io.BytesIO() as output_img_buffer,
        ):
            game_over_card_template = Image.open(img_buffer)

            game_over_card_image = image_edit_service.add_text(
                game_over_card_template,
                str(final_score),
                text_size=128,
                position=(0, 10),
                center=True,
            )
            game_over_card_image.save(output_img_buffer, format="PNG")

            output_img_buffer.seek(0)
            output_img_bytes = output_img_buffer.read()

    return BufferedInputFile(output_img_bytes, filename="game_over_card.png")


async def edit_game_scores_card(
    image_edit_service: ImageEditService,
    game_session: GameSession,
    app_settings: Settings,
) -> BufferedInputFile:
    score_records = [
        f"{i + 1}. {timestamp} - {score} point(s)"
        for i, (score, timestamp) in enumerate(
            sorted(game_session.score_board.items(), key=lambda x: x[0], reverse=True)
        )
    ]

    game_scores_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_scores.png"
    )

    async with aiofiles.open(game_scores_template_path, "rb") as template_file:
        template_image_bytes = await template_file.read()

        with (
            io.BytesIO(template_image_bytes) as img_buffer,
            io.BytesIO() as output_img_buffer,
        ):
            game_scores_card_template = Image.open(img_buffer)
            game_scores_image = image_edit_service.add_multiline_text(
                game_scores_card_template,
                score_records,
                text_size=48,
                position=(0, 0),
                center=True,
            )

            game_scores_image.save(output_img_buffer, format="PNG")

            output_img_buffer.seek(0)
            output_img_bytes = output_img_buffer.read()

    return BufferedInputFile(output_img_bytes, filename="game_scores.png")


async def edit_quiz_game_card(
    image_edit_service: ImageEditService,
    game_session: GameSession,
    app_settings: Settings,
    round_facts: List[str],
) -> BufferedInputFile:
    quiz_card_template_path = os.path.join(
        app_settings.assets_folder, "cards", "game_guessing.png"
    )

    heart_icon_path = os.path.join(app_settings.assets_folder, "icons", "heart.png")

    async with (
        aiofiles.open(quiz_card_template_path, "rb") as template_file,
        aiofiles.open(heart_icon_path, "rb") as heart_icon,
    ):
        template_image_bytes = await template_file.read()
        heart_icon_bytes = await heart_icon.read()

        with (
            io.BytesIO(template_image_bytes) as img_buffer,
            io.BytesIO(heart_icon_bytes) as heart_icon_buffer,
            io.BytesIO() as output_img_buffer,
        ):
            quiz_card_template = Image.open(img_buffer)
            heart_icon = Image.open(heart_icon_buffer)

            numerated_text = [
                f"{i + 1}. {chunk}" for i, chunk in enumerate(round_facts)
            ]
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

            quiz_card_image.save(output_img_buffer, format="PNG")

            output_img_buffer.seek(0)
            output_img_bytes = output_img_buffer.read()

    return BufferedInputFile(output_img_bytes, filename="quiz_card.png")
