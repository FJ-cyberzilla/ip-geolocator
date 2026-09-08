import pytest
from ip_geolocator.middleware.ip_extractor import IPExtractorMiddleware

def test_extract_ip_from_x_forwarded_for():
    middleware = IPExtractorMiddleware()
    headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
    assert middleware.extract_ip(headers) == "1.2.3.4"

def test_extract_ip_from_x_real_ip():
    middleware = IPExtractorMiddleware()
    headers = {"X-Real-IP": "8.8.8.8"}
    assert middleware.extract_ip(headers) == "8.8.8.8"

def test_extract_ip_no_headers():
    middleware = IPExtractorMiddleware()
    headers = {}
    assert middleware.extract_ip(headers) is None
