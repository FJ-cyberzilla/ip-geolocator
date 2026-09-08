import ipaddress
from typing import Optional


def validate_ip(ip: str) -> Optional[str]:
    """
    Validates an IP address string.
    Returns normalized IP string if valid, None otherwise.
    """
    try:
        addr = ipaddress.ip_address(ip)
        return str(addr)
    except ValueError:
        return None
