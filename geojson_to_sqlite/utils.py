# import shapely
import sqlite_utils


def import_features(db_path, table, features, spatialite=False, spatialite_mode=None):
    db = sqlite_utils.Database(db_path)

    def yield_records():
        for feature in features:
            record = feature.get("properties") or {}
            record["geometry"] = feature["geometry"]
            yield record

    db[table].insert_all(yield_records())
    return db[table]
