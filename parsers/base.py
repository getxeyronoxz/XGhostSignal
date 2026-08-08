from abc import ABC, abstractmethod
from typing import List, Dict, Any
import datetime

class BaseParser(ABC):
    """
    Abstract BaseParser ensuring all ingested RF/Telecom data normalizes 
    into a unified schema before database storage.
    """

    def __init__(self):
        self.source_type = self.__class__.__name__

    def create_unified_record(
        self,
        timestamp: str = None,
        source: str = None,
        protocol: str = "",
        frequency: str = "",
        mcc: str = "",
        mnc: str = "",
        lac_tac: str = "",
        cell_id: str = "",
        latitude: str = "",
        longitude: str = "",
        signal_strength: str = "",
        confidence: str = "high"
    ) -> Dict[str, Any]:
        """
        Creates a strictly normalized dictionary for the parser engine.
        """
        if not timestamp:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not source:
            source = self.source_type

        return {
            "timestamp": timestamp,
            "source": source,
            "protocol": protocol,
            "frequency": frequency,
            "mcc": mcc,
            "mnc": mnc,
            "lac_tac": lac_tac,
            "cell_id": cell_id,
            "latitude": latitude,
            "longitude": longitude,
            "signal_strength": signal_strength,
            "confidence": confidence
        }

    @abstractmethod
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read the file and return a list of unified records.
        """
        pass
