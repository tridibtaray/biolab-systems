# Leave this file empty or use it to expose classes
from .database import Database
from .auth import AuthManager

import logging
import sys
from pathlib import Path

# Create a logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("biolab.log"), # Saves to a file
        logging.StreamHandler(sys.stdout)      # Still prints to terminal
    ]
)

logger = logging.getLogger("BioLab")
logger.info("BioLab System logging initialized.")
