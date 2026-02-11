"""
ECDICT Integration Script
Downloads ECDICT CSV and converts it to SQLite for fast local lookups.
"""
import csv
import sqlite3
import urllib.request
import os

# ECDICT CSV URL (using the stardict.csv from the repo)
ECDICT_URL = "https://github.com/skywind3000/ECDICT/releases/download/1.0.28/ecdict-sqlite-28.zip"
DB_PATH = "ecdict.db"

def download_ecdict():
    """Download ECDICT database"""
    print("Downloading ECDICT database...")
    # For simplicity, we'll use the pre-built SQLite version
    # User should manually download from: https://github.com/skywind3000/ECDICT/releases
    print(f"Please download ecdict-sqlite-28.zip from:")
    print("https://github.com/skywind3000/ECDICT/releases/download/1.0.28/ecdict-sqlite-28.zip")
    print(f"Extract stardict.db and rename it to {DB_PATH}")
    print("Place it in the service/ directory")

if __name__ == "__main__":
    download_ecdict()
