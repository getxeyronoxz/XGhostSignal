"""ADS-B (Automatic Dependent Surveillance-Broadcast) Parser for XGhostSignal

This module provides real ADS-B data streaming from dump1090/readsb servers.
ADS-B is used by aircraft to broadcast their position, altitude, speed, etc.

Connection: Typically dump1090 exposes a TCP port (30003) for basestation format.
"""
from typing import Dict, Any, Optional
from .base import BaseParser
import socket
import time


class ADSBParser(BaseParser):
    """Live streaming interface for ADS-B aviation feeds.

    Connects to dump1090/readsb TCP ports (default: 30003) to receive
    real-time aircraft position data in basestation format.

    Basestation format (CSV):
    message_type,transmission_type,session_id,aircraft_id,hex_id,flight_id,
    date_utc,time_utc,latitude,longitude,altitude,ground_speed,track,vertical_rate,some_fields
    """

    def __init__(self):
        super().__init__()
        self.connected = False
        self.socket = None

    def parse_file(self, file_path: str) -> list:
        """Parse ADS-B data from a file.

        Args:
            file_path: Path to ADS-B data file (CSV format)

        Returns:
            List of normalized observation records
        """
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split(',')
                    if len(parts) < 15:
                        continue

                    # Parse basestation format
                    msg_type = parts[0]
                    hex_id = parts[4] if len(parts) > 4 else None
                    flight_id = parts[5] if len(parts) > 5 else None
                    lat = parts[7] if len(parts) > 7 else None
                    lon = parts[8] if len(parts) > 8 else None
                    alt = parts[9] if len(parts) > 9 else None
                    speed = parts[10] if len(parts) > 10 else None

                    if lat and lon:
                        record = self.create_unified_record(
                            source=file_path,
                            protocol="ADS-B",
                            frequency="1090000000",
                            cell_id=hex_id,
                            latitude=lat,
                            longitude=lon,
                            confidence="high"
                        )
                        records.append(record)

        except Exception as e:
            print(f"[-] Error parsing ADS-B file: {e}")

        return records

    def connect(self, host: str = "127.0.0.1", port: int = 30003, timeout: int = 10) -> bool:
        """Connect to ADS-B data source.

        Args:
            host: Hostname of dump1090/readsb server
            port: TCP port (default 30003)
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        if self.connected:
            return True

        try:
            self.socket = socket.create_connection((host, port), timeout=timeout)
            self.socket.setblocking(False)
            self.connected = True
            print(f"[*] Connected to ADS-B server at {host}:{port}")
            return True
        except socket.error as e:
            print(f"[-] Failed to connect to ADS-B server: {e}")
            return False

    def read_messages(self, max_messages: int = 100) -> list:
        """Read ADS-B messages from connected server.

        Args:
            max_messages: Maximum messages to read

        Returns:
            List of raw message strings
        """
        if not self.connected:
            return []

        messages = []
        try:
            while len(messages) < max_messages:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    messages.extend(data.decode('utf-8').strip().split('\n'))
                except socket.error:
                    # No data available yet
                    break
        except Exception as e:
            print(f"[-] Error reading ADS-B messages: {e}")

        return messages

    def parse_messages(self, messages: list) -> list:
        """Parse raw ADS-B messages into normalized records.

        Args:
            messages: List of raw ADS-B message strings

        Returns:
            List of normalized observation records
        """
        records = []
        for msg in messages:
            msg = msg.strip()
            if not msg or msg.startswith('#'):
                continue

            parts = msg.split(',')
            if len(parts) < 15:
                continue

            # Extract fields
            msg_type = parts[0]
            hex_id = parts[4] if len(parts) > 4 else None
            lat = parts[7] if len(parts) > 7 else None
            lon = parts[8] if len(parts) > 8 else None
            alt = parts[9] if len(parts) > 9 else None

            if lat and lon and hex_id:
                record = self.create_unified_record(
                    source="adsb-dump1090",
                    protocol="ADS-B",
                    frequency="1090000000",
                    cell_id=hex_id,
                    latitude=lat,
                    longitude=lon,
                    signal_strength=alt,
                    confidence="high"
                )
                records.append(record)

        return records

    def start_stream(self, host: str = "127.0.0.1", port: int = 30003, duration: int = None):
        """Start continuous ADS-B stream.

        Args:
            host: ADS-B server hostname
            port: ADS-B server port
            duration: Stream duration in seconds (None for infinite)
        """
        if not self.connect(host, port):
            print("[-] Cannot start stream: connection failed")
            return

        start_time = time.time()
        message_count = 0

        print(f"[*] Streaming ADS-B data from {host}:{port}")
        print("[*] Press Ctrl+C to stop")

        try:
            while True:
                # Check duration
                if duration and (time.time() - start_time) > duration:
                    break

                # Read available messages
                messages = self.read_messages()
                if messages:
                    records = self.parse_messages(messages)
                    message_count += len(records)

                    # Save to database
                    if records:
                        from core.database import SessionLocal, Entity, Observation
                        session = SessionLocal()
                        try:
                            for record in records:
                                entity_value = record.get('cell_id')
                                if entity_value:
                                    entity = session.query(Entity).filter_by(value=entity_value).first()
                                    if not entity:
                                        entity = Entity(
                                            type="AIRCRAFT",
                                            value=entity_value,
                                            normalized_value=entity_value,
                                            source="adsb-stream"
                                        )
                                        session.add(entity)
                                        session.commit()
                                        session.refresh(entity)

                                    obs = Observation(
                                        entity_id=entity.id,
                                        observation_type="ADS-B",
                                        protocol="ADS-B",
                                        frequency=record.get('frequency'),
                                        cell_id=entity_value,
                                        latitude=float(record['latitude']) if record.get('latitude') else None,
                                        longitude=float(record['longitude']) if record.get('longitude') else None,
                                        confidence=record.get('confidence'),
                                        source="adsb-dump1090"
                                    )
                                    session.add(obs)
                            session.commit()
                        finally:
                            session.close()

                    for record in records:
                        lat = record.get('latitude', 'N/A')
                        lon = record.get('longitude', 'N/A')
                        print(f"[ADS-B] {record['cell_id']} | {lat},{lon}")

                else:
                    # No data, small sleep
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[*] Stopping ADS-B stream...")
        finally:
            self.stop()
            print(f"[*] Total messages processed: {message_count}")

    def stop(self):
        """Close connection and cleanup."""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None


# Module-level singleton
adsb_parser = ADSBParser()
