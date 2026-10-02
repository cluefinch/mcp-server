import gzip
import ipaddress
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_search import fetcher, security


class _SingleChunkStream(httpx.AsyncByteStream):
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    async def __aiter__(self):
        yield self.payload


@pytest.mark.parametrize(
    "payload",
    [
        gzip.compress(b"research material")[:-4],
        gzip.compress(b"first member") + gzip.compress(b"second member"),
    ],
)
async def test_invalid_gzip_stream_shapes_are_rejected(payload):
    response = httpx.Response(
        200, headers={"content-encoding": "gzip"}, stream=_SingleChunkStream(payload)
    )

    with pytest.raises(fetcher.FetchError) as caught:
        await fetcher._read_limited(response)

    assert caught.value.kind == "invalid_content"


@pytest.mark.parametrize(
    "host",
    [
        "2130706433",  # single-integer spelling of 127.0.0.1
        "0x7f000001",  # hexadecimal spelling accepted by some resolvers
        "127.1",  # shortened dotted spelling of 127.0.0.1
        "0177.0.0.1",  # legacy octal-like spelling accepted by some resolvers
    ],
)
async def test_alternate_numeric_ipv4_forms_fail_closed_after_resolution(
    monkeypatch, host
):
    resolve = AsyncMock(return_value={ipaddress.ip_address("127.0.0.1")})
    monkeypatch.setattr(security, "_resolve_host", resolve)

    with pytest.raises(security.SecurityError):
        await security.validate_url(f"http://{host}/")

    resolve.assert_awaited_once_with(host)


async def test_redirect_target_with_alternate_numeric_ipv4_is_revalidated(monkeypatch):
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://2130706433/"})

    async def resolve(host):
        if host == "2130706433":
            return {ipaddress.ip_address("127.0.0.1")}
        return {ipaddress.ip_address("8.8.8.8")}

    monkeypatch.setattr(security, "_resolve_host", resolve)
    monkeypatch.setattr(
        fetcher, "_client", httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )

    with pytest.raises(security.SecurityError):
        await fetcher._download("https://example.com/")

    assert len(calls) == 1
