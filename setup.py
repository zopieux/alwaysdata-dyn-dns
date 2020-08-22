from setuptools import setup, find_packages

setup(
    name="alwaysdata-dyn-dns",
    author="Alexandre Macabies",
    version="1.0.0",
    description="Lightweight HTTP server to update Alwaysdata DNS entries, "
    "typically from a dynamic DNS client such as a home router.",
    license="MIT",
    url="https://github.com/zopieux/alwaysdata-dyn-dns/",
    install_requires=["aiohttp"],
    packages=find_packages(),
)
