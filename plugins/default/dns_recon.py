import socket

PLUGIN_NAME = "dns_recon_basic"
VERSION = "1.0.0"

def run(domain: str) -> dict:
    """
    Performs basic local DNS resolution mapping for a domain.
    """
    try:
        ip = socket.gethostbyname(domain)
        return {
            "status": "success",
            "domain": domain,
            "resolved_ip": ip
        }
    except socket.gaierror:
        return {"status": "error", "message": "Failed to resolve domain."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
