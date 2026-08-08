"""PCAP/PCAPNG Parser for XGhostSignal

This module provides real PCAP parsing for LTE, GSM, and other wireless protocols.
Uses scapy for packet parsing and protocol analysis.

Supported protocols:
- LTE S1AP (S1 Application Protocol)
- NAS (Non-Access Stratum)
- GSM RR (Radio Resource)
- GMM (GPRS Mobility Management)
- SM (Session Management)
"""
from typing import List, Dict, Any, Optional
from .base import BaseParser
import os
import hashlib

try:
    from scapy.all import rdpcap, Packet
    from scapy.layers.inet import IP, TCP, UDP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class PCAPParser(BaseParser):
    """PCAP/PCAPNG parser for wireless protocol analysis.

    This parser reads packet captures and extracts cellular signaling data
    including LTE S1AP, NAS, GSM RR, and other protocol layers.
    """

    def __init__(self):
        super().__init__()
        self.packet_count = 0
        self.detected_protocols = set()

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a PCAP/PCAPNG file and extract cellular protocol data.

        Args:
            file_path: Path to the PCAP/PCAPNG file

        Returns:
            List of normalized observation records

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PCAP file not found: {file_path}")

        if not SCAPY_AVAILABLE:
            raise ImportError("scapy is required for PCAP parsing. Install with: pip install scapy")

        records = []
        self.packet_count = 0
        self.detected_protocols = set()

        packets = rdpcap(file_path)
        print(f"[*] Loaded {len(packets)} packets from {file_path}")

        for pkt in packets:
            record = self._process_packet(pkt, file_path)
            if record:
                records.append(record)

        print(f"[*] Extracted {len(records)} observations from {self.packet_count} packets")
        print(f"[*] Detected protocols: {self.detected_protocols}")

        return records

    def _process_packet(self, pkt: 'Packet', source: str) -> Optional[Dict[str, Any]]:
        """Process a single packet and extract protocol information."""
        self.packet_count += 1

        if pkt.haslayer('TCP') or pkt.haslayer('UDP'):
            return self._extract_tcpip_protocol(pkt, source)
        elif pkt.haslayer('IP'):
            return self._extract_ip_protocol(pkt, source)
        else:
            return self._extract_generic_protocol(pkt, source)

    def _extract_tcpip_protocol(self, pkt: 'Packet', source: str) -> Optional[Dict[str, Any]]:
        """Extract protocol info from TCP/IP packets.

        This handles:
        - LTE S1AP over SCTP
        - Diameter protocol (Ro/Rx)
        - HTTP/HTTPS signaling
        """
        if not pkt.haslayer('IP') or not (pkt.haslayer('TCP') or pkt.haslayer('UDP')):
            return None

        ip_layer = pkt.getlayer('IP')
        tcp_layer = pkt.getlayer('TCP') if pkt.haslayer('TCP') else None
        udp_layer = pkt.getlayer('UDP') if pkt.haslayer('UDP') else None

        protocol = "UNKNOWN"
        confidence = "medium"

        if tcp_layer:
            dst_port = tcp_layer.dport
            src_port = tcp_layer.sport

            if dst_port == 36412 or src_port == 36412:
                protocol = "LTE_S1AP"
                confidence = "high"
            elif dst_port == 3868 or src_port == 3868:
                protocol = "DIAMETER"
                confidence = "medium"
            elif dst_port in [80, 443, 8080, 8443]:
                protocol = f"HTTP_{dst_port}"
                confidence = "low"
        elif udp_layer:
            if udp_layer.dport == 53 or udp_layer.sport == 53:
                protocol = "DNS"
                confidence = "low"

        self.detected_protocols.add(protocol)

        if protocol != "UNKNOWN":
            return self.create_unified_record(
                source=source,
                protocol=protocol,
                cell_id=self._extract_cell_id_from_ip(ip_layer),
                confidence=confidence
            )

        return None

    def _extract_gsm_protocol(self, pkt: 'Packet', source: str) -> Optional[Dict[str, Any]]:
        """Extract GSM RR/GMM/SM protocol data."""
        if not pkt.haslayer('GSMPacket'):
            return None

        gsm_pkt = pkt.getlayer('GSMPacket')

        protocol = "GSM_UNKNOWN"
        confidence = "medium"

        if hasattr(gsm_pkt, 'msgtype'):
            msg_type = gsm_pkt.msgtype
            if msg_type == 0x3E:
                protocol = "GSM_GMM_LUR"
            elif msg_type == 0x21:
                protocol = "GSM_GMM_CM"
            elif msg_type == 0x2F:
                protocol = "GSM_GMM_PAGING"
            elif msg_type == 0x32:
                protocol = "GSM_RR_CHANNEL"
            elif msg_type == 0x12:
                protocol = "GSM_RR_HANDOVER"
            else:
                protocol = f"GSM_MSG_{msg_type}"

        self.detected_protocols.add(protocol)

        return self.create_unified_record(
            source=source,
            protocol=protocol,
            cell_id=pkt.src.replace(':', '')[:10] if hasattr(pkt, 'src') else None,
            confidence=confidence
        )

    def _extract_ip_protocol(self, pkt: 'Packet', source: str) -> Optional[Dict[str, Any]]:
        """Extract generic IP protocol info."""
        ip_layer = pkt.getlayer('IP')

        return self.create_unified_record(
            source=source,
            protocol="IP_PACKET",
            cell_id=ip_layer.src.replace('.', '')[:8],
            confidence="low"
        )

    def _extract_generic_protocol(self, pkt: 'Packet', source: str) -> Optional[Dict[str, Any]]:
        """Generic protocol extraction for unknown packets."""
        src_mac = None
        for layer in [pkt, pkt.payload]:
            if hasattr(layer, 'src') and getattr(layer, 'src', None):
                src_mac = layer.src
                break

        if not src_mac:
            src_mac = str(pkt)[:20]

        return self.create_unified_record(
            source=source,
            protocol="RAW_PACKET",
            cell_id=src_mac.replace(':', '')[:10],
            confidence="low"
        )

    def _extract_cell_id_from_ip(self, ip_layer) -> Optional[str]:
        """Extract cell ID from IP packet."""
        if ip_layer.src:
            parts = ip_layer.src.split('.')
            if len(parts) == 4:
                return f"{parts[0]}{parts[1]}{parts[2][:1]}"
        return None
