# Configure these settings for document analysis as you see fit -Z

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent # <- will just alias JEEAnalyzer (or whatever you save this project as) dir as project_root
DATA_DIR = PROJECT_ROOT / "data" # Same concept as above, but just alias' the data sub directories
RAW_PDF_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"

# If there's a directory that doesn't exist, create it:
for directory in [RAW_PDF_DIR, EXTRACTED_DIR, PROCESSED_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Name DB
DATABASE_PATH = DATABASE_DIR / "epstein_docs.db"

# Able to use these options: "pypdf", "pdfplumber", "pymupdf"
PDF_EXTRACTION_METHOD = "pymupdf"

# General logging:
LOG_LEVEL = "INFO"
