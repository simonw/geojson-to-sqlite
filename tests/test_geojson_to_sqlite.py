from click.testing import CliRunner
from dirty_equals import IsApprox
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
    assert len(rows) == 2
    uk, usa = rows
    assert uk["slug"] == "uk"
    assert usa["slug"] == "usa"
    assert json.loads(uk["geometry"]) == {
        "type": "Polygon",
        "coordinates": [
            [
                [IsApprox(-8.0859374), IsApprox(60.93043220292332)],
                [IsApprox(-16.875), IsApprox(50.28933925329177)],
                [IsApprox(-5.9765625), IsApprox(48.92249926375824)],
                [IsApprox(4.21875), IsApprox(52.26815737376816)],
                [IsApprox(1.0546875), IsApprox(60.06484046010452)],
                [IsApprox(-8.0859375), IsApprox(60.93043220292332)],
            ]
        ],
    }
    assert json.loads(usa["geometry"]) == {
        "type": "Polygon",
        "coordinates": [
            [
                [IsApprox(-129.375), IsApprox(47.75409797968003)],
                [IsApprox(-119.53125), IsApprox(33.43144133557529)],
                [IsApprox(-96.6796875), IsApprox(25.48295117535531)],
                [IsApprox(-85.4296875), IsApprox(24.20688962239802)],
                [IsApprox(-77.34374999999998), IsApprox(25.48295117535531)],
                [IsApprox(-61.52343749999999), IsApprox(44.33956524809713)],
                [IsApprox(-84.375), IsApprox(51.39920565355377)],
                [IsApprox(-100.8984375), IsApprox(50.06419173665909)],
                [IsApprox(-115.3125), IsApprox(50.73645513701067)],
                [IsApprox(-129.375), IsApprox(47.75409797968003)],
            ]
        ],
    }
    initial_rows = db.execute_returning_dicts(
        "select slug, AsGeoJSON(geometry) as geometry from features"
    )
    assert ["slug"] == db["features"].pks
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
    # Rows should have stayed the same
    assert initial_rows == db.execute_returning_dicts(
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


def test_bundle_properties(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--properties",
        ],
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert ["features"] == db.table_names()

    assert db["features"].columns_dict == {
        "properties": str,
        "geometry": str,
    }


def test_bundle_properties_colname(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--properties",
            "props",
        ],
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert ["features"] == db.table_names()

    assert db["features"].columns_dict == {
        "props": str,
        "geometry": str,
    }


@pytest.mark.skipif(not utils.find_spatialite(), reason="Could not find SpatiaLite")
def test_bundle_properties_spatialite(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli,
        [
            db_path,
            "features",
            str(testdir / "feature-collection.geojson"),
            "--properties",
            "--spatialite",
        ],
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    assert "features" in db.table_names()

    assert db["features"].columns_dict == {
        "properties": str,
        "geometry": float,  # no idea why this is float, but it's consistent
    }
