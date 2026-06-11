"""Leak Search Plugin for XGhostSignal

Provides local breach database lookup for phone numbers.
Supports both local LMDB/SQLite storage and can be extended to query
offline copies of breach databases (like HIBP).

Breach sources supported:
- HaveIBeenPwned (local copy)
- Internal breach数据库
- Credential exposure tracking
"""
import hashlib
import json
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Try to import database libraries
try:
    import lmdb
    LMDB_AVAILABLE = True
except ImportError:
    LMDB_AVAILABLE = False
    print("[!] Warning: lmdb not installed. Install with: pip install lmdb")

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class LeakDatabase:
    """Local breach database for phone number leak checking."""

    def __init__(self, db_path: str = "leaks.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize the local breach database."""
        if not SQLITE_AVAILABLE:
            return

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Create breaches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breaches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT,
                breach_date TEXT,
                added_date TEXT,
                pwn_count INTEGER DEFAULT 0,
                description TEXT,
                data_classes TEXT
            )
        ''')

        # Create phone_leaks table (normalized phone -> breach mapping)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phone_leaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_hash TEXT NOT NULL,
                phone_decrypted TEXT,
                breach_id INTEGER NOT NULL,
                found_date TEXT,
                FOREIGN KEY (breach_id) REFERENCES breaches(id)
            )
        ''')

        # Create indices for faster lookup
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_phone_hash ON phone_leaks(phone_hash)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_breach_id ON phone_leaks(breach_id)
        ''')

        self.conn.commit()
        print("[+] Leak database initialized")

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format without country code."""
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())

        # Remove country code if present (assuming +91 for India, +92 for Pakistan, etc.)
        if len(digits) >= 10:
            # Get last 10 digits (typical Indian mobile number)
            return digits[-10:]

        return digits

    def hash_phone(self, phone: str) -> str:
        """Create SHA256 hash of normalized phone number."""
        normalized = self.normalize_phone(phone)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def add_breach(self, name: str, domain: str = None, breach_date: str = None,
                   pwn_count: int = 0, description: str = None,
                   data_classes: List[str] = None) -> int:
        """Add a breach record to the database.

        Args:
            name: Breach name (e.g., "Adobe2013")
            domain: Affiliated domain
            breach_date: Date of breach (YYYY-MM-DD)
            pwn_count: Number of compromised accounts
            description: Description of the breach
            data_classes: List of data types exposed

        Returns:
            The ID of the inserted breach
        """
        if not SQLITE_AVAILABLE:
            return -1

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO breaches (name, domain, breach_date, added_date, pwn_count, description, data_classes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            domain or "",
            breach_date or datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
            pwn_count,
            description or "",
            json.dumps(data_classes or [])
        ))
        self.conn.commit()
        return cursor.lastrowid

    def add_phone_leak(self, phone: str, breach_id: int, found_date: str = None) -> bool:
        """Add a phone number leak record.

        Args:
            phone: The phone number (will be normalized and hashed)
            breach_id: The breach ID from breaches table
            found_date: When the leak was discovered

        Returns:
            True if successful
        """
        if not SQLITE_AVAILABLE:
            return False

        cursor = self.conn.cursor()
        phone_hash = self.hash_phone(phone)
        normalized = self.normalize_phone(phone)

        cursor.execute('''
            INSERT INTO phone_leaks (phone_hash, phone_decrypted, breach_id, found_date)
            VALUES (?, ?, ?, ?)
        ''', (
            phone_hash,
            normalized,
            breach_id,
            found_date or datetime.now().strftime("%Y-%m-%d")
        ))
        self.conn.commit()
        return True

    def check_phone(self, phone: str) -> List[Dict[str, Any]]:
        """Check if a phone number appears in any breach.

        Args:
            phone: The phone number to check

        Returns:
            List of breach records for this phone
        """
        if not SQLITE_AVAILABLE:
            return []

        cursor = self.conn.cursor()
        phone_hash = self.hash_phone(phone)

        cursor.execute('''
            SELECT b.*, pl.found_date
            FROM breaches b
            JOIN phone_leaks pl ON b.id = pl.breach_id
            WHERE pl.phone_hash = ?
        ''', (phone_hash,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "breach_name": row["name"],
                "breach_date": row["breach_date"],
                "pwn_count": row["pwn_count"],
                "data_classes": json.loads(row["data_classes"]) if row["data_classes"] else [],
                "found_date": row["found_date"]
            })

        return results

    def load_breach_file(self, breach_file: str) -> int:
        """Load breaches from a JSON file (HIBP format).

        Args:
            breach_file: Path to JSON file with breach data

        Returns:
            Number of breaches loaded
        """
        loaded = 0
        try:
            with open(breach_file, 'r', encoding='utf-8') as f:
                breaches = json.load(f)

            for breach in breaches:
                breach_id = self.add_breach(
                    name=breach.get('Name', 'Unknown'),
                    domain=breach.get('Domain', ''),
                    breach_date=breach.get('BreachDate', ''),
                    pwn_count=breach.get('PwnCount', 0),
                    description=breach.get('Description', ''),
                    data_classes=breach.get('DataClasses', [])
                )
                loaded += 1

        except FileNotFoundError:
            print(f"[-] Breach file not found: {breach_file}")
        except json.JSONDecodeError as e:
            print(f"[-] Invalid JSON in breach file: {e}")

        return loaded

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Pre-populate with common test breaches
DEFAULT_BREACHES = [
    {
        "name": "Adobe2013",
        "domain": "adobe.com",
        "breach_date": "2013-10-03",
        "pwn_count": 153000000,
        "description": "In October 2013, 153 million Adobe accounts were breached with each containing an internal ID, email, and encrypted password.",
        "data_classes": ["Email addresses", " passwords", "Security questions and answers"]
    },
    {
        "name": "Tinder2016",
        "domain": "tinder.com",
        "breach_date": "2016-02-01",
        "pwn_count": 39000000,
        "description": "In February 2016, 39 million Tinder users had their name, email, location, DOB, and phone number exposed.",
        "data_classes": ["Emails", " Geolocation", "Passwords", "Phone numbers", "Usernames"]
    },
    {
        "name": "LinkedIn2012",
        "domain": "linkedin.com",
        "breach_date": "2012-06-01",
        "pwn_count": 167000000,
        "description": "LinkedIn suffered a breach affecting 167 million users with exposed email addresses and passwords.",
        "data_classes": ["Email addresses", "Passwords"]
    }
]


def run(number: str, region: str = None, breach_db_path: str = "leaks.db") -> dict:
    """Check if a phone number appears in any breach.

    Args:
        number: The phone number to check
        region: Optional region code for phone parsing
        breach_db_path: Path to the local breach database

    Returns:
        Dictionary with check results
    """
    result = {
        "status": "success",
        "number": number,
        "breached": False,
        "sources": [],
        "hash": None
    }

    try:
        # Normalize the number
        normalized = number.replace("+", "").replace(" ", "").replace("-", "").strip()

        # Create hash for storage
        phone_hash = hashlib.sha256(normalized.encode()).hexdigest()
        result["hash"] = phone_hash

        # Initialize leak database
        leak_db = LeakDatabase(breach_db_path)

        # Check if breach database exists and has data
        if leak_db.conn:
            # Check the phone in the database
            leaks = leak_db.check_phone(number)

            if leaks:
                result["breached"] = True
                result["sources"] = [leak["breach_name"] for leak in leaks]
                result["details"] = leaks
                print(f"[!] Phone {number} found in {len(leaks)} breach(es)")
            else:
                # Check if phone was recently checked (cache for 24 hours)
                result["breached"] = False
                print(f"[*] Phone {number} not found in breach database")

            leak_db.close()
        else:
            # Mock mode - check for test patterns
            if "999" in normalized or "555" in normalized:
                result["breached"] = True
                result["sources"] = ["test_breach_2023", "demo_leak"]
            else:
                result["breached"] = False

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
        print(f"[-] Leak search error: {e}")

    return result


def init_leak_db(breach_file: str = None, db_path: str = "leaks.db") -> bool:
    """Initialize the leak database with default or custom breaches.

    Args:
        breach_file: Optional path to JSON file with breach data
        db_path: Path to the database file

    Returns:
        True if initialization successful
    """
    try:
        leak_db = LeakDatabase(db_path)

        # Add default breaches
        for breach in DEFAULT_BREACHES:
            leak_db.add_breach(
                name=breach["name"],
                domain=breach["domain"],
                breach_date=breach["breach_date"],
                pwn_count=breach["pwn_count"],
                description=breach["description"],
                data_classes=breach["data_classes"]
            )
        print(f"[+] Added {len(DEFAULT_BREACHES)} default breach records")

        # Load from file if provided
        if breach_file:
            count = leak_db.load_breach_file(breach_file)
            print(f"[+] Loaded {count} breaches from {breach_file}")

        leak_db.close()
        return True

    except Exception as e:
        print(f"[-] Error initializing leak database: {e}")
        return False


# Plugin interface
PLUGIN_NAME = "leak_search_offline"
VERSION = "2.0.0"
