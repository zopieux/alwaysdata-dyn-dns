import argparse
import logging
import os

from aiohttp import web

from alwaysdata_dyn_dns import create_app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    p = argparse.ArgumentParser()
    p.add_argument("--host", default="::")  # IPv6 is required.
    p.add_argument("--port", type=int, default=os.environ.get("PORT", 8888))
    p.add_argument(
        "--ttl",
        type=int,
        default=300,
        help="TTL (seconds) to use for missing entries",
    )
    p.add_argument("--add", action="store_true", help="create missing entries")
    p.add_argument(
        "--domain",
        type=int,
        required=True,
        help="target top-level domain (Alwaysdata numeric domain id)",
    )
    p.add_argument("--account", required=True, help="Alwaysdata account name")
    p.add_argument("--key", required=True, help="Alwaysdata API key")
    p.add_argument("--name", required=True, help="target host name")
    p.add_argument(
        "--password", help="optional password to be checked as password="
    )
    args = p.parse_args()

    app = create_app(args)
    web.run_app(app, host=args.host, port=args.port, print=None)
