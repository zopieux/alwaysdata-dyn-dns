from argparse import Namespace

import pytest
from aioresponses import aioresponses

from alwaysdata_dyn_dns import create_app


@pytest.fixture
def args():
    return Namespace(
        domain=12321,
        ttl=4242,
        account="dupond",
        key="secret",
        name="ns.foo.bar",
        password="banana",
    )


@pytest.fixture
def expect():
    # Pass-through aiohttp_client test webserver itself.
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        yield m


async def test_wrong_password(aiohttp_client, args):
    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get("/")
    assert r.status == 403
    assert "invalid password" in await r.text()


async def test_no_ip(aiohttp_client, args):
    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get("/", params={"password": args.password})
    assert r.status == 400
    assert "at least ?ip= or ?ip6=" in await r.text()


async def test_invalid_ip4(aiohttp_client, args):
    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "192.168.1"}
    )
    assert r.status == 400
    assert "invalid ?ip=" in await r.text()


async def test_invalid_ip6(aiohttp_client, args):
    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip6": "fe80:beer:1"}
    )
    assert r.status == 400
    assert "invalid ?ip6=" in await r.text()


async def test_no_add_no_create_ip4(aiohttp_client, args, expect):
    args.add = False

    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321", payload=[]
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "1.2.3.4"}
    )
    assert r.status == 204


async def test_create_ip4(aiohttp_client, args, expect):
    args.add = True

    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321", payload=[]
    )
    expect.post(
        "https://api.alwaysdata.com/v1/record/",
        status=204,
        # payload={
        #     "domain": "12321",
        #     "type": "A",
        #     "name": "ns.foo.bar",
        #     "value": "1.2.3.4",
        #     "ttl": 4242,
        # },
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "1.2.3.4"}
    )
    assert r.status == 204


async def test_create_ip4_failure(aiohttp_client, args, expect):
    args.add = True

    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321", payload=[]
    )
    expect.post(
        "https://api.alwaysdata.com/v1/record/", status=403,
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "1.2.3.4"}
    )
    assert r.status == 500


async def test_create_ip6(aiohttp_client, args, expect):
    args.add = True

    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321", payload=[]
    )
    expect.post(
        "https://api.alwaysdata.com/v1/record/",
        status=204,
        # payload={
        #     "domain": "12321",
        #     "type": "AAAA",
        #     "name": "ns.foo.bar",
        #     "value": "fe80::1",
        #     "ttl": 4242,
        # },
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip6": "fe80::1"}
    )
    assert r.status == 204


async def test_create_both_ip4_ip6(aiohttp_client, args, expect):
    args.add = True

    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321", payload=[]
    )
    expect.post(
        "https://api.alwaysdata.com/v1/record/",
        status=204,
        # payload={
        #     "domain": "12321",
        #     "type": "A",
        #     "name": "ns.foo.bar",
        #     "value": "1.2.3.4",
        #     "ttl": 4242,
        # },
    )
    expect.post(
        "https://api.alwaysdata.com/v1/record/",
        status=204,
        # payload={
        #     "domain": "12321",
        #     "type": "AAAA",
        #     "name": "ns.foo.bar",
        #     "value": "fe80::1",
        #     "ttl": 4242,
        # },
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/",
        params={"password": args.password, "ip": "1.2.3.4", "ip6": "fe80::1"},
    )
    assert r.status == 204


async def test_update_ip4(aiohttp_client, args, expect):
    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321",
        payload=[
            {
                "href": "/v1/record/13371337",
                "type": "A",
                "value": "4.3.2.1",
                "name": "ns.foo.bar",
                "is_user_defined": True,
                "ttl": 1337,
            }
        ],
    )
    expect.patch(
        "https://api.alwaysdata.com/v1/record/13371337",
        status=204,
        # payload={"value": "1.2.3.4"},
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "1.2.3.4"}
    )
    assert r.status == 204


async def test_update_ip4_failure(aiohttp_client, args, expect):
    expect.get(
        "https://api.alwaysdata.com/v1/record/?domain=12321",
        payload=[
            {
                "href": "/v1/record/13371337",
                "type": "A",
                "value": "4.3.2.1",
                "name": "ns.foo.bar",
                "is_user_defined": True,
                "ttl": 1337,
            }
        ],
    )
    expect.patch(
        "https://api.alwaysdata.com/v1/record/13371337", status=403,
    )

    app = create_app(args)
    client = await aiohttp_client(app)

    r = await client.get(
        "/", params={"password": args.password, "ip": "1.2.3.4"}
    )
    assert r.status == 500
