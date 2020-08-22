import ipaddress
import logging

import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)

API_BASE = "https://api.alwaysdata.com"
API_RECORD = API_BASE + "/v1/record/"


async def patch_record(s, record: dict, address: str):
    logger.info("Patching record %r with address %s", record, address)
    async with s.patch(API_BASE + record["href"], json={"value": address}):
        pass


async def create_record(s, record: dict):
    logger.info("Creating record %r", record)
    async with s.post(API_RECORD, json=record):
        pass


async def handle_request(request):
    args = request.app["args"]
    domain = str(args.domain)

    if args.password and args.password != request.query.get("password"):
        logger.debug("invalid password")
        return web.Response(status=403, text="invalid password")

    qs = {
        "A": ("ip", ipaddress.IPv4Address),
        "AAAA": ("ip6", ipaddress.IPv6Address),
    }

    new_addresses = {}
    for record_type, (arg, parser) in qs.items():
        try:
            new_addresses[record_type] = str(parser(request.query[arg]))
        except KeyError:
            pass
        except ValueError:
            return web.Response(status=400, text=f"invalid ?{arg}=")

    if not new_addresses:
        args = " or ".join(f"?{arg}=" for arg, _ in qs.values())
        return web.Response(status=400, text=f"at least {args} is required")

    auth = aiohttp.BasicAuth(f"{args.key} account={args.account}")

    async with aiohttp.ClientSession(auth=auth, raise_for_status=True) as s:
        # Find existing A and AAAA records for this domain & name.
        async with s.get(API_RECORD, params={"domain": domain}) as r:
            existing_records = [
                record
                for record in (await r.json())
                if record["is_user_defined"]
                and record["name"] == args.name
                and record["type"] in qs.keys()
            ]
        existing_records = {r["type"]: r for r in existing_records}

        # Add or update the records.
        for record_type, address in new_addresses.items():
            record = existing_records.get(record_type)
            if record is not None:
                await patch_record(s, record, address)

            elif not args.add:
                logger.warning(
                    "--add not specified, not creating record %s %s",
                    record_type,
                    address,
                )

            else:
                await create_record(
                    s,
                    {
                        "domain": domain,
                        "name": args.name,
                        "ttl": args.ttl,
                        "type": record_type,
                        "value": address,
                    },
                )

    return web.Response(status=204)


def create_app(args):
    app = web.Application()
    app["args"] = args
    app.add_routes([web.get("/", handle_request)])
    return app
