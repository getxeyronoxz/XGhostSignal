"""
Configuration and constraints for XGhostSignal.
Strictly scoped to India, Pakistan, China, USA, and Russia.
"""

from typing import List

# Allowed Mobile Country Codes for tower dataset filtering
ALLOWED_MCCS: List[int] = [
    404, 405, # India
    410,      # Pakistan
    460,      # China
    310, 311, 312, 313, 314, 315, 316, # USA
    250       # Russia
]

# Allowed ISO-3166-1 alpha-2 country codes for phonenumbers parsing
ALLOWED_COUNTRY_CODES: List[str] = [
    "IN", # India
    "PK", # Pakistan
    "CN", # China
    "US", # USA
    "RU"  # Russia
]

# Database settings
DB_PATH = "sqlite:///xghostsignal.db"
