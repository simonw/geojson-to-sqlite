from click.testing import CliRunner
from geojson_to_sqlite import cli, utils
import pytest
import sqlite_utils
import pathlib


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
def test_single_feature_spatialite(tmpdir):
    db_path = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli.cli, [db_path, "features", str(testdir / "feature.geojson"), "--spatialite"]
    )
    assert 0 == result.exit_code, result.stdout
    db = sqlite_utils.Database(db_path)
    utils.init_spatialite(db, utils.find_spatialite())
    assert {"features", "spatial_ref_sys"}.issubset(db.table_names())
    rows = db.execute_returning_dicts(
        "select slug, AsGeoJSON(geometry) as geometry from features"
    )
    assert [
        {
            "slug": "uk",
            "geometry": '{"type":"Polygon","coordinates":[[[-8.0859375,60.93043220292332],[-16.875,50.28933925329177],[-5.9765625,48.92249926375824],[4.21875,52.26815737376816],[1.0546875,60.06484046010452],[-8.0859375,60.93043220292332]]]}',
        }
    ] == rows


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
