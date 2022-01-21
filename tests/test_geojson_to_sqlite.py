from click.testing import CliRunner
from geojson_to_sqlite import cli, utils
import pytest
import sqlite_utils
import pathlib
import json


testdir = pathlib.Path(__file__).parent


def test_invalid(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "invalid.geojson")]
    )
    assert 1 == result.exit_code
    assert (
        "Error: GeoJSON must be a Feature or a FeatureCollection"
        == result.stdout.strip()
    )


def test_single_feature(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "feature.geojson")]
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert ["features"] == db.table_names()
    rows = list(db["features"].rows)
    assert [
        {
            "slug": "uk",
            "description": "Rough area around the UK",
            "geometry": '{"type": "Polygon", "coordinates": [[[-8.0859375, 60.930432202923335], [-16.875, 50.28933925329178], [-5.9765625, 48.922499263758255], [4.21875, 52.26815737376817], [1.0546875, 60.06484046010452], [-8.0859375, 60.930432202923335]]]}',
        }
    ] == rows


@pytest.mark.skipif(not utils.find_spatialite(), reason="Could not find SpatiaLite")
def test_feature_collection_spatialite(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--spatialite",
            "--alter",
            "--pk=slug",
        ],
        catch_exceptions=False,
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    utils.init_spatialite(db, utils.find_spatialite())
    assert {"features", "spatial_ref_sys"}.issubset(db.table_names())
    rows = db.execute_returning_dicts(
        "select slug, AsGeoJSON(geometry) as geometry from features"
    )
    expected_rows = [
        {
            "slug": "uk",
            "geometry": '{"type":"Polygon","coordinates":[[[-8.0859375,60.93043220292332],[-16.875,50.28933925329177],[-5.9765625,48.92249926375824],[4.21875,52.26815737376816],[1.0546875,60.06484046010452],[-8.0859375,60.93043220292332]]]}',
        },
        {
            "slug": "usa",
            "geometry": '{"type":"Polygon","coordinates":[[[-129.375,47.75409797968003],[-119.53125,33.43144133557529],[-96.6796875,25.48295117535531],[-85.4296875,24.20688962239802],[-77.34374999999998,25.48295117535531],[-61.52343749999999,44.33956524809713],[-84.375,51.39920565355377],[-100.8984375,50.06419173665909],[-115.3125,50.73645513701067],[-129.375,47.75409797968003]]]}',
        },
    ]
    assert ["slug"] == db["features"].pks
    assert expected_rows == rows
    # Run it once more to check that upserting should work
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--spatialite",
            "--alter",
            "--pk=slug",
        ],
        catch_exceptions=False,
    )
    assert 0 == result.exit_code
    assert expected_rows == db.execute_returning_dicts(
        "select slug, AsGeoJSON(geometry) as geometry from features"
    )


@pytest.mark.skipif(not utils.find_spatialite(), reason="Could not find SpatiaLite")
@pytest.mark.parametrize("use_spatial_index", (True, False))
def test_spatial_index(tmpdir, use_spatial_index):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
        ]
        + (["--spatial-index"] if use_spatial_index else ["--spatialite"]),
        catch_exceptions=False,
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    utils.init_spatialite(db, utils.find_spatialite())
    has_idx = "idx_features_geometry" in db.table_names()
    assert has_idx == use_spatial_index
    has_spatial_index_geometry_columns = bool(
        list(db["geometry_columns"].rows_where("spatial_index_enabled = 1"))
    )
    assert has_spatial_index_geometry_columns == use_spatial_index


def test_feature_collection(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "feature-collection.geojson")]
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert ["features"] == db.table_names()
    rows = list(db["features"].rows)
    assert [
        {
            "slug": "uk",
            "description": "Rough area around the UK",
            "geometry": '{"type": "Polygon", "coordinates": [[[-8.0859375, 60.930432202923335], [-16.875, 50.28933925329178], [-5.9765625, 48.922499263758255], [4.21875, 52.26815737376817], [1.0546875, 60.06484046010452], [-8.0859375, 60.930432202923335]]]}',
            "continent": None,
        },
        {
            "slug": "usa",
            "description": "Very rough area around the USA",
            "geometry": '{"type": "Polygon", "coordinates": [[[-129.375, 47.754097979680026], [-119.53125, 33.43144133557529], [-96.6796875, 25.48295117535531], [-85.4296875, 24.206889622398023], [-77.34374999999999, 25.48295117535531], [-61.52343749999999, 44.33956524809713], [-84.375, 51.39920565355378], [-100.8984375, 50.064191736659104], [-115.31249999999999, 50.736455137010665], [-129.375, 47.754097979680026]]]}',
            "continent": "North America",
        },
    ] == rows
    assert ["rowid"] == db["features"].pks


def test_feature_collection_pk_and_alter(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "feature.geojson"), "--pk=slug"]
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert ["features"] == db.table_names()
    rows = db.execute_returning_dicts("select slug, description from features")
    assert [{"slug": "uk", "description": "Rough area around the UK"}] == rows
    assert ["slug"] == db["features"].pks

    # Running it again should insert usa
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--pk=slug",
            "--alter",
        ],
    )
    assert 0 == result.exit_code, result.stdout
    rows = db.execute_returning_dicts("select slug, description from features")
    assert [
        {"slug": "uk", "description": "Rough area around the UK"},
        {"slug": "usa", "description": "Very rough area around the USA"},
    ] == rows


def test_feature_collection_id_as_pk(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "feature-collection-ids.geojson")]
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    features = db["features"]

    # check that we're setting the right pk
    assert "id" in features.columns_dict and ["id"] == features.pks

    uk = features.get(3)
    usa = features.get(8)

    assert "uk" == uk["slug"]
    assert "usa" == usa["slug"]

    assert [c.name for c in features.columns] == [
        "id",
        "slug",
        "description",
        "geometry",
        "continent",
    ]


def test_feature_collection_override_id(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection-ids.geojson"),
            "--pk=slug",
        ],
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    features = db["features"]

    assert ["slug"] == features.pks

    uk = features.get("uk")
    usa = features.get("usa")

    assert "Rough area around the UK" == uk["description"]
    assert "North America" == usa["continent"]


def test_ndjson(tmpdir):
    ndjson = testdir / "quakes.ndjson"
    db_path = str(tmpdir / "output.db")

    with open(ndjson) as f:
        data = [json.loads(line) for line in f]

    result = CliRunner().invoke(cli.cli, [db_path, "features", str(ndjson), "--nl"])
    assert 0 == result.exit_code, result.stdout

    db = sqlite_utils.Database(db_path)
    features = db["features"]

    assert features.count == 44

    # the quakes dataset has an id attribute set,
    # so check that we're setting the right pk
    assert "id" in features.columns_dict and ["id"] == features.pks


@pytest.mark.skipif(not utils.find_spatialite(), reason="Could not find SpatiaLite")
def test_ndjson_with_spatial_index(tmpdir):
    ndjson = testdir / "quakes.ndjson"
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(ndjson), "--nl", "--spatial-index"]
    )
    assert 0 == result.exit_code, result.stdout
    # There should be a spatial index
    db = sqlite_utils.Database(db_path)
    utils.init_spatialite(db, utils.find_spatialite())
    has_spatial_index_geometry_columns = bool(
        list(db["geometry_columns"].rows_where("spatial_index_enabled = 1"))
    )
    assert has_spatial_index_geometry_columns
    # And 44 rows in the quakes table
    assert db["features"].count == 44


def test_missing_geometry(tmpdir):
    quakes = testdir / "quakes.geojson"
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(cli.cli, [db_path, "features", str(quakes)])

    assert 0 == result.exit_code, result.stdout

    db = sqlite_utils.Database(db_path)
    assert db["features"].count == 10

    # this should have a null geometry
    rows = list(db["features"].rows)
    nulls = [row for row in rows if row["geometry"] is None]

    assert len(rows) == 10
    assert len(nulls) == 2
