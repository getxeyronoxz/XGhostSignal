import csv
from typing import List, Dict, Any
from .base import BaseParser

class RtlPowerParser(BaseParser):
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 7: continue
                # rtl_power format: date, time, hz_low, hz_high, hz_step, samples, dbm...
                date_str = row[0].strip()
                time_str = row[1].strip()
                hz_low = row[2].strip()
                # grab the max power seen across the bins
                dbm_values = [float(x) for x in row[6:] if x.strip()]
                max_dbm = str(max(dbm_values)) if dbm_values else ""
                
                record = self.create_unified_record(
                    timestamp=f"{date_str}T{time_str}Z",
                    source="rtl_power",
                    protocol="RF_SPECTRUM",
                    frequency=hz_low,
                    signal_strength=max_dbm,
                    confidence="medium"
                )
                records.append(record)
        return records
