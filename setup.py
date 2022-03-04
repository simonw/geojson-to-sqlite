from setuptools import setup
import os

VERSION = "1.0"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="geojson-to-sqlite",
    description="CLI tool for converting GeoJSON to SQLite (optionally with SpatiaLite)",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/geojson-to-sqlite",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["geojson_to_sqlite"],
    entry_points="""
        [console_scripts]
        geojson-to-sqlite=geojson_to_sqlite.cli:cli
    """,
    install_requires=["sqlite-utils>=2.2", "shapely"],
    extras_require={"test": ["pytest", "dirty-equals"]},
)
