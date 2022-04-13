from shapely.geometry import shape
import sqlite_utils
from sqlite_utils.utils import find_spatialite

import inspect
import itertools
import json
import os


class SpatiaLiteError(Exception):
    pass


def yield_records(features, pk, properties, spatialite):
    for feature in features:
        record = {}
        if "id" in feature:
            record["id"] = feature["id"]
        if properties:
            record[properties] = feature.get("properties") or {}
        else:
            record.update(feature.get("properties") or {})
        geometry = feature.get("geometry")
        if spatialite and geometry:
            geometry = shape(geometry).wkt

        record["geometry"] = geometry
        yield record


def import_features(
    db_path,
    table,
    features,
    pk=None,
    alter=False,
    properties="",
    spatialite=False,
    spatialite_mod=None,
    spatial_index=False,
):
    db = sqlite_utils.Database(db_path)
    features = iter(features)

    # grab a sample, for checking ids
    sample_geojson = list(itertools.islice(features, 100))
    features = itertools.chain(sample_geojson, features)
    sample_records = list(yield_records(sample_geojson, pk, properties, spatialite))

    if pk is None and has_ids(sample_records):
        pk = "id"

    conversions = {}
    if spatialite_mod or spatial_index:
        spatialite = True

    if spatialite:
        lib = spatialite_mod or find_spatialite()

        if not lib:
            raise SpatiaLiteError("Could not find SpatiaLite module")

        db.init_spatialite(lib)

        if table not in db.table_names():
            # Create the table, using detected column types
            column_types = sqlite_utils.suggest_column_types(sample_records)
            column_types.pop("geometry")
            remove_tmp_column = False
            if not column_types:
                column_types["_tmp"] = str
                remove_tmp_column = True
            db[table].create(column_types, pk=pk)
            ensure_table_has_geometry(db, table)
            if remove_tmp_column:
                db[table].transform(drop={"_tmp"})

        conversions = {"geometry": "GeomFromText(?, 4326)"}

    if pk:
        db[table].upsert_all(
            yield_records(features, pk, properties, spatialite),
            conversions=conversions,
            pk=pk,
            alter=alter,
        )

    else:
        db[table].insert_all(
            yield_records(features, pk, properties, spatialite), conversions=conversions
        )

    if spatial_index:
        # db.conn.execute("select CreateSpatialIndex(?, ?)", [table, "geometry"])
        db[table].create_spatial_index("geometry")

    return db[table]


def get_features(geojson_file, nl=False):
    """
    Get a list of features from something resembling geojson.

    Note that if the `nl` option is True, this will return a generator
    that yields a single feature from each line in the source file.
    """
    if nl:
        return (json.loads(line) for line in geojson_file if line.strip())

    # if not nl, load the whole file
    geojson = json.load(geojson_file)
    if not isinstance(geojson, dict):
        raise TypeError("GeoJSON root must be an object")

    if geojson.get("type") not in ("Feature", "FeatureCollection"):
        raise ValueError("GeoJSON must be a Feature or a FeatureCollection")

    if geojson["type"] == "Feature":
        return [geojson]

    return geojson.get("features", [])


def ensure_table_has_geometry(db, table):
    if "geometry" not in db[table].columns_dict:
        db[table].add_geometry_column("geometry", "GEOMETRY")


def has_ids(features):
    return all(f.get("id") is not None for f in features)
