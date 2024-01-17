import os

TOP_SCORES = 10
DEFAULT_INIT_LIVES = 5
DEFAULT_FACTS_NUM = 5
DEFAULT_OPTIONS_NUM = 4

COUNTRY_NAMES_FILE_LOCATION = (
    os.getenv("VAR_COUNTRY_NAMES_FILE_LOCATION") or "./data/dev/names.json"
)
COUNTRY_FACTS_FILE_LOCATION = (
    os.getenv("VAR_COUNTRY_FACTS_FILE_LOCATION") or "./data/dev/facts.json"
)

TOKEN = os.getenv("VAR_TOKEN") or ""
