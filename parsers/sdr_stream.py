"""RTL-SDR Hardware Streaming Parser for XGhostSignal

This module provides real RTL-SDR hardware integration for live RF signal capture.
Requires: pyrtlsdr package and connected RTL-SDR USB dongle.
"""
from typing import Dict, Any, Optional, Callable
from .base import BaseParser
import time
import threading
import math

# Optional import - will fail gracefully if not installed
try:
    from rtlsdr import RtlSdr
    RTLSDR_AVAILABLE = True
except ImportError:
    RTLSDR_AVAILABLE = False
    print("[!] Warning: pyrtlsdr not installed. Install with: pip install pyrtlsdr")


class SDRStreamParser(BaseParser):
    """Live streaming interface for RTL-SDR hardware.

    This parser continuously samples RF data and detects signal bursts
    across cellular bands (700MHz - 2.6GHz depending on hardware).
    """

    def __init__(self):
        super().__init__()
        self.is_streaming = False
        self.sdr: Optional[RtlSdr] = None
        self.center_freq = 900e6  # Default: GSM 900 MHz
        self.sample_rate = 2.4e6  # Default: 2.4 MSps
        self.gain = 40  # Default: 40 dB
        self.buffer_size = 1024

    def setup_sdr(self, center_freq: float = 900e6, sample_rate: float = 2.4e6,
                  gain: int = 40, bandwidth: Optional[float] = None) -> bool:
        """Initialize and configure RTL-SDR hardware.

        Args:
            center_freq: Center frequency in Hz (default: 900MHz for GSM)
            sample_rate: Sample rate in Hz (default: 2.4MSps)
            gain: LNA gain in dB (0-50, default: 40)
            bandwidth: IF bandwidth in Hz (None for auto)

        Returns:
            True if SDR initialized successfully, False otherwise
        """
        if not RTLSDR_AVAILABLE:
            print("[-] Error: pyrtlsdr not installed")
            return False

        try:
            self.sdr = RtlSdr()
            self.sdr.sample_rate = sample_rate
            self.sdr.center_freq = center_freq
            self.sdr.gain = gain
            if bandwidth:
                self.sdr.bandwidth = bandwidth
            self.sdr.freq_corr = 0  # Set PPM correction if needed
            self.center_freq = center_freq
            self.sample_rate = sample_rate
            self.gain = gain
            print(f"[*] RTL-SDR initialized: {sample_rate/1e6:.1f} MSPS @ {center_freq/1e6:.1f} MHz")
            return True
        except Exception as e:
            print(f"[-] Failed to initialize RTL-SDR: {e}")
            return False

    def read_samples(self, num_samples: int = 1024) -> Optional[bytes]:
        """Read raw IQ samples from SDR.

        Args:
            num_samples: Number of samples to read (must be power of 2)

        Returns:
            Raw IQ bytes or None on error
        """
        if not self.sdr:
            return None
        try:
            samples = self.sdr.read_bytes(num_samples)
            return samples
        except Exception as e:
            print(f"[-] Error reading samples: {e}")
            return None

    def calculate_power_dbm(self, i_samples: list, q_samples: list) -> float:
        """Calculate average power in dBm from IQ samples.

        Args:
            i_samples: In-phase samples
            q_samples: Quadrature samples

        Returns:
            Average power in dBm
        """
        if not i_samples or not q_samples:
            return -100.0  # Default low power

        # Calculate power for each sample
        powers = [(i**2 + q**2) for i, q in zip(i_samples, q_samples)]
        avg_power = sum(powers) / len(powers)

        # Convert to dBm (assuming 1 ohm impedance and 1V reference)
        if avg_power > 0:
            dbm = 10 * math.log10(avg_power) + 30  # +30 for mW reference
        else:
            dbm = -100.0

        return dbm

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse file is not supported for live streaming.

        Use start_stream() for live RTL-SDR capture instead.
        """
        return []

    def _process_samples(self, samples: bytes, freq_offset: float = 0):
        """Process raw IQ samples and create observation records.

        Args:
            samples: Raw IQ bytes
            freq_offset: Frequency offset correction
        """
        if len(samples) < 2:
            return

        # Parse IQ samples (8-bit I and Q)
        num_samples = len(samples) // 2
        i_samples = []
        q_samples = []

        for i in range(num_samples):
            # Convert unsigned 8-bit to signed (-128 to 127)
            i_val = (samples[2*i] - 128) / 128.0
            q_val = (samples[2*i + 1] - 128) / 128.0
            i_samples.append(i_val)
            q_samples.append(q_val)

        # Calculate power
        power_dbm = self.calculate_power_dbm(i_samples, q_samples)

        # Detect signal burst (threshold: -50 dBm)
        BURST_THRESHOLD = -50.0
        if power_dbm > BURST_THRESHOLD:
            actual_freq = self.center_freq + freq_offset

            record = self.create_unified_record(
                source="rtl-sdr-live",
                protocol="RF_BURST",
                frequency=str(actual_freq),
                signal_strength=f"{power_dbm:.2f}",
                confidence="high"
            )

            # Save to database
            from core.database import SessionLocal, Entity, Observation
            session = SessionLocal()
            try:
                entity_value = f"EMITTER_RF_BURST_{int(actual_freq)}"
                entity = session.query(Entity).filter_by(value=entity_value).first()
                if not entity:
                    entity = Entity(
                        type="RF_EMITTER",
                        value=entity_value,
                        normalized_value=entity_value,
                        source="sdr_stream"
                    )
                    session.add(entity)
                    session.commit()
                    session.refresh(entity)

                obs = Observation(
                    entity_id=entity.id,
                    observation_type="RF_BURST",
                    protocol="RF_BURST",
                    frequency=str(actual_freq),
                    signal_strength=f"{power_dbm:.2f}",
                    confidence="high",
                    source="rtl-sdr-live"
                )
                session.add(obs)
                session.commit()
                print(f"[SDR DETECT] {int(actual_freq/1e6):.2f} MHz | {power_dbm:.1f} dBm")
            finally:
                session.close()

    def start_stream(self, center_freq: float = 900e6, sample_rate: float = 2.4e6,
                     gain: int = 40, duration: float = None, callback: Callable = None):
        """Start continuous RTL-SDR streaming and signal detection.

        Args:
            center_freq: Center frequency in Hz (default: 900MHz GSM)
            sample_rate: Sample rate in Hz (default: 2.4MSps)
            gain: LNA gain in dB (default: 40)
            duration: Stream duration in seconds (None for infinite)
            callback: Optional callback(record) for each detection
        """
        if not RTLSDR_AVAILABLE:
            print("[-] Error: pyrtlsdr not installed")
            print("[*] Install with: pip install pyrtlsdr")
            print("[*] Also ensure RTL-SDR drivers are installed:")
            print("    - Windows: Install Zadig (https://zadig.akeo.ie) -> LibUSB Win32")
            print("    - Linux: Add udev rules for RTL2832U")
            return

        if not self.setup_sdr(center_freq, sample_rate, gain):
            return

        self.is_streaming = True
        start_time = time.time()
        sample_count = 0

        print(f"[*] Starting RTL-SDR stream on {center_freq/1e6:.1f} MHz")
        print(f"[*] Press Ctrl+C to stop")

        try:
            while self.is_streaming:
                # Check duration limit
                if duration and (time.time() - start_time) > duration:
                    break

                # Read samples
                samples = self.read_samples(self.buffer_size)
                if samples is None:
                    time.sleep(0.1)
                    continue

                sample_count += len(samples)

                # Process samples
                self._process_samples(samples)

                # Call callback if provided
                if callback:
                    callback(samples)

                # Small delay to prevent overwhelming CPU
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n[*] Stopping RTL-SDR stream...")
        finally:
            self.stop()

    def stop(self):
        """Stop streaming and cleanup SDR resources."""
        self.is_streaming = False
        if self.sdr:
            try:
                self.sdr.close()
                print("[*] RTL-SDR device closed")
            except Exception as e:
                print(f"[-] Error closing SDR: {e}")
            self.sdr = None


# Module-level singleton
sdr_stream = SDRStreamParser()
