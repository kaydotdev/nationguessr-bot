import os
from enum import Enum

from pydantic import Field, NonNegativeInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingLevel(Enum):
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FactsGenerationStrategy(str, Enum):
    LOCAL_ZIPFILE = "LOCAL_ZIPFILE"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VAR_", case_sensitive=False)

    logging_level: LoggingLevel = Field(default=LoggingLevel.INFO)

    default_top_scores: NonNegativeInt = Field(default=10)
    default_init_lives: NonNegativeInt = Field(default=5)
    default_facts_num: NonNegativeInt = Field(default=5)
    default_options_num: NonNegativeInt = Field(default=4)
    default_countries_num: NonNegativeInt = Field(default=194)

    token: str = Field(...)
    secret_token: str | None = Field(default=None)
    assets_folder: str | os.PathLike = Field(default="./assets")

    fact_generation_strategy: FactsGenerationStrategy = Field(
        FactsGenerationStrategy.LOCAL_ZIPFILE
    )

    aws_access_key: str = Field(...)
    aws_secret_key: str = Field(...)
    aws_fsm_table_name: str = Field(...)
    aws_region: str = Field(...)
