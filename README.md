# geojson-to-sqlite

[![PyPI](https://img.shields.io/pypi/v/geojson-to-sqlite.svg)](https://pypi.org/project/geojson-to-sqlite/)
[![CircleCI](https://circleci.com/gh/simonw/geojson-to-sqlite.svg?style=svg)](https://circleci.com/gh/simonw/geojson-to-sqlite)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/geojson-to-sqlite/blob/master/LICENSE)

CLI tool for converting GeoJSON to SQLite (optionally with SpatiaLite)

[RFC 7946: The GeoJSON Format](https://tools.ietf.org/html/rfc7946)

**Status:** Under heavy development.

## How to install

    $ pip install geojson-to-sqlite

## How to use

You can run this tool against a GeoJSON file like so:

    $ geojson-to-sqlite my.db features features.geojson

This will load all of the features from the `features.geojson` file into a table called `features`.

Each row will have a `geometry` column containing the feature geometry, and columns for each of the keys found in any `properties` attached to those features.

The table will be created the first time you run the command.

On subsequent runs you can use the `--alter` option to add any new columns that are missing from the table.

If your features have an `"id"` property it will be used as the primary key for the table. You can also use `--pk=PROPERTY` with the name of a property to use that as the primary key.

If no primary key is specified, a SQLite `rowid` column will be used.

You can use `-` as the filename to import from standard input. For example:

    $ curl https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_20m.json \
        | geojson-to-sqlite my.db states - --pk GEO_ID

## Using with SpatiaLite

By default, the `geometry` column will contain JSON.

If you have installed the [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) module for SQLite you can instead import the geometry into a geospatially indexed column.

You can do this using the `--spatialite` option, like so:

    $ geojson-to-sqlite my.db features features.geojson --spatialite

The tool will search for the SpatiaLite module in the following locations:

* `/usr/lib/x86_64-linux-gnu/mod_spatialite.so`
* `/usr/local/lib/mod_spatialite.dylib`

If you have installed the module in another location, you can use the `--spatialite_mod=xxx` option to specify where:

    $ geojson-to-sqlite my.db features features.geojson \
        --spatialite_mod=/usr/lib/mod_spatialite.dylib
