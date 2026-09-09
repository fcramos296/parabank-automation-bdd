import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_URL: str = os.getenv("BASE_URL", "https://parabank.parasoft.com/parabank")
    SCRAPE_DO_TOKEN: str = os.getenv("SCRAPE_DO_TOKEN", "07e4b7b63db3400a905484f7138b69f20bf3a82d039")
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    BROWSER: str = os.getenv("BROWSER", "chromium")

settings = Settings()