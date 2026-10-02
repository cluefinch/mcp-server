import ipaddress
from unittest.mock import AsyncMock, Mock

import httpcore
import httpx
import pytest

from mcp_search import security, transport


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com",
        "http://localhost",
        "https://user:pass@example.com",
        "http://foo.localhost",
        "http://127.0.0.1",
        "http://192.168.1.1",
        "http://100.64.0.1",
        "http://[::1]",
        "http://[::ffff:127.0.0.1]",
        "http://[::7f00:1]",
        "http://0.0.0.0",
        "http://224.0.0.1",
        "http://[ff02::1]",
        "http://[64:ff9b::7f00:1]",
        "http://[2002:7f00:1::]",
        "https://example.com:99999",
        "https://[",
    ],
)
async def test_blocked_urls(url):
    with pytest.raises(security.SecurityError):
        await security.validate_url(url)


@pytest.mark.parametrize("host", ["2130706433", "017700000001", "0x7f000001", "127.1"])
async def test_alternate_numeric_ipv4_forms_are_dns_checked_and_blocked(
    monkeypatch, host
):
    resolve = AsyncMock(return_value={ipaddress.ip_address("127.0.0.1")})
    monkeypatch.setattr(security, "_resolve_host", resolve)

    with pytest.raises(security.SecurityError):
        await security.validate_url(f"http://{host}/")

    resolve.assert_awaited_once_with(host)


async def test_mixed_dns_rejected(monkeypatch):
    monkeypatch.setattr(
        security,
        "_resolve_host",
        AsyncMock(
            return_value={
                ipaddress.ip_address("8.8.8.8"),
                ipaddress.ip_address("127.0.0.1"),
            }
        ),
    )
    with pytest.raises(security.SecurityError):
        await security.validate_url("https://example.com")


async def test_reserved_ipv6_from_dns_rejected(monkeypatch):
    monkeypatch.setattr(
        security,
        "_resolve_host",
        AsyncMock(return_value={ipaddress.ip_address("::7f00:1")}),
    )
    with pytest.raises(security.SecurityError):
        await security.validate_url("https://example.com")


async def test_connection_pins_checked_address(monkeypatch):
    resolve = AsyncMock(return_value={ipaddress.ip_address("8.8.8.8")})
    monkeypatch.setattr(security, "_resolve_host", resolve)
    backend = transport.ValidatedBackend()
    backend.backend = AsyncMock()
    await backend.connect_tcp("example.com", 443)
    assert resolve.await_count == 1
    assert backend.backend.connect_tcp.call_args.args == ("8.8.8.8", 443)


async def test_rebinding_rejected_at_connection(monkeypatch):
    resolve = AsyncMock(
        side_effect=[
            {ipaddress.ip_address("8.8.8.8")},
            {ipaddress.ip_address("127.0.0.1")},
        ]
    )
    monkeypatch.setattr(security, "_resolve_host", resolve)
    await security.validate_url("https://example.com")
    backend = transport.ValidatedBackend()
    backend.backend = AsyncMock()
    with pytest.raises(security.SecurityError):
        await backend.connect_tcp("example.com", 443)
    backend.backend.connect_tcp.assert_not_called()


async def test_transport_preserves_tls_hostname_and_host_header(monkeypatch):
    monkeypatch.setattr(
        security,
        "_resolve_host",
        AsyncMock(return_value={ipaddress.ip_address("8.8.8.8")}),
    )
    stream = Mock(spec=httpcore.AsyncNetworkStream)
    stream.read = AsyncMock(
        return_value=b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"
    )
    stream.write = AsyncMock()
    stream.aclose = AsyncMock()
    stream.start_tls = AsyncMock(return_value=stream)
    stream.get_extra_info.return_value = None
    connect = AsyncMock(return_value=stream)
    backend = transport.ValidatedBackend()
    backend.backend = AsyncMock(connect_tcp=connect)
    monkeypatch.setattr(transport, "ValidatedBackend", lambda: backend)
    async with httpx.AsyncClient(transport=transport.SafeTransport()) as client:
        response = await client.get("https://example.com/path")
    assert response.text == "ok"
    assert connect.call_args.args == ("8.8.8.8", 443)
    assert stream.start_tls.call_args.kwargs["server_hostname"] == "example.com"
    assert b"Host: example.com" in b"".join(
        call.args[0] for call in stream.write.call_args_list
    )
