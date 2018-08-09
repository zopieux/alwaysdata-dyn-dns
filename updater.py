#!/usr/bin/eval PYTHON_VERSION=3.7 python

import argparse
import aiohttp
import ipaddress
import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)

API_BASE = 'https://api.alwaysdata.com'
API_RECORD = API_BASE + '/v1/record/'


async def handle_request(request):
    args = request.app['args']

    if args.password and args.password != request.query.get('password'):
        logger.warning("invalid password")
        return web.Response(status=403, text="invalid password")

    qs = {'A': ('ip', ipaddress.IPv4Address),
          'AAAA': ('ip6', ipaddress.IPv6Address)}
    ips = {}

    for type, (arg, parser) in qs.items():
        try:
            ips[type] = str(parser(request.query.get(arg)))
        except ValueError:
            pass

    if not ips:
        args = ' or '.join(f'?{arg}=' for arg, _ in qs.values())
        return web.Response(status=400, text=f"at least {args} is required")

    auth = aiohttp.BasicAuth(f'{args.key} account={args.account}')

    async with aiohttp.ClientSession(auth=auth) as s:
        # get existing A and AAAA records for this domain & name
        async with s.get(API_RECORD, params={'domain': args.domain}) as r:
            existing_records = [record for record in (await r.json())
                                if record['is_user_defined']
                                and record['name'] == args.name
                                and record['type'] in qs.keys()]

        # delete them
        for record in existing_records:
            href = record['href']
            logger.info("deleting record type: %s, name: %s",
                record['type'], record['name'])
            async with s.delete(API_BASE + href, auth=auth) as r:
                if not (200 <= r.status < 300):
                    logger.error("could not delete record %s (%s)",
                        href, r.status)

        # then add the updated one(s)
        for type, ip in ips.items():
            record = {
                'domain': args.domain,
                'name': args.name,
                'ttl': args.ttl,
                'type': type,
                'value': ip,
            }
            logger.info("adding record %s", record)
            async with s.post(API_RECORD, json=record) as r:
                if not (200 <= r.status < 300):
                    logger.error("could not add record %s (%s)",
                        record, r.status)

    return web.Response(status=204)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    p = argparse.ArgumentParser()
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', type=int, default=os.environ.get('PORT', 8888))
    p.add_argument('--ttl', type=int, default=300)
    p.add_argument('--domain', type=int, required=True,
        help="target A domain (alwaysdata domain id)")
    p.add_argument('--name', required=True, help="target A record subdomain")
    p.add_argument('--key', required=True, help="alwaysdata API key")
    p.add_argument('--account', required=True, help="alwaysdata account name")
    p.add_argument('--password',
        help="optional password to be checked as password=")
    args = p.parse_args()

    app = web.Application()
    app['args'] = args
    app.add_routes([web.get('/', handle_request)])

    web.run_app(app, host=args.host, port=args.port, print=None)
