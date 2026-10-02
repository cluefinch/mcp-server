import asyncio
import socket
import time

import pytest

from mcp_search.limits import RequestLimiter


@pytest.fixture(autouse=True)
async def forbid_dns(monkeypatch):
    def unexpected_dns(*args, **kwargs):
        raise AssertionError("Limiter identity must not resolve DNS")

    monkeypatch.setattr(socket, "getaddrinfo", unexpected_dns)
    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", unexpected_dns)


@pytest.mark.parametrize(
    "first,second,host",
    [
        ("https://faß.de/a", "https://xn--fa-hia.de/b", "xn--fa-hia.de"),
        ("https://faß.de./a", "http://XN--FA-HIA.DE:8080/b", "xn--fa-hia.de"),
        ("https://EXAMPLE.COM./a", "http://example.com:8080/b", "example.com"),
        ("https://8.8.8.8/a", "http://8.8.8.8:8080/b", "8.8.8.8"),
        (
            "https://[2001:4860:ABCD::8888]/a",
            "http://[2001:4860:abcd::8888]:8080/b",
            "2001:4860:abcd::8888",
        ),
    ],
)
async def test_equivalent_hostnames_share_lock_and_spacing(first, second, host):
    limiter = RequestLimiter(concurrency=2, interval=0.02)
    attempted = asyncio.Event()
    entered = asyncio.Event()
    starts = []

    async def wait():
        attempted.set()
        async with limiter.request(second):
            starts.append(time.monotonic())
            entered.set()

    task = None
    try:
        async with limiter.request(first):
            starts.append(time.monotonic())
            task = asyncio.create_task(wait())
            await asyncio.wait_for(attempted.wait(), timeout=1)
            assert not entered.is_set()
            assert list(limiter.hosts) == [host]
            assert limiter.hosts[host].users == 2
        await asyncio.wait_for(task, timeout=1)
        assert entered.is_set()
        assert starts[1] - starts[0] >= 0.019
    finally:
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_idna_does_not_merge_sharp_s_with_ascii_ss():
    limiter = RequestLimiter(concurrency=2, interval=0)
    async with limiter.request("https://faß.de/"):
        async with asyncio.timeout(1):
            async with limiter.request("https://fass.de/"):
                assert set(limiter.hosts) == {"xn--fa-hia.de", "fass.de"}


@pytest.mark.parametrize(
    "host", ["2001:4860:4860:0:0:0:0:8888", "2001:4860:4860::8888"]
)
async def test_ipv6_preserves_httpx_host_representation(host):
    limiter = RequestLimiter(interval=0)
    async with limiter.request(f"https://[{host}]/"):
        assert list(limiter.hosts) == [host]
