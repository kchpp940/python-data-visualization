from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent
_CODE_DIR = _PROJECT_ROOT / "code"

DATA_DIR = _CODE_DIR / "data"
RAW_DATA_DIR = _CODE_DIR / "data" / "raw"
IMAGES_DIR = _CODE_DIR / "images"


def epa_fuel_economy():
    return RAW_DATA_DIR / "EPA_fuel_economy.csv"


def epa_fuel_economy_summary():
    return RAW_DATA_DIR / "EPA_fuel_economy_summary.csv"


def amazon_books():
    return RAW_DATA_DIR / "AmazonBooks.xlsx"