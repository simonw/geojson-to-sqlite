import click
import sqlite_utils
import json
from . import utils


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", required=True)
@click.argument("geojson", type=click.File(), required=True)
@click.option("--pk", help="Column to use as a primary key")
@click.option("--alter", is_flag=True, help="Add any missing columns")
@click.option("--spatialite", is_flag=True, help="Use SpatiaLite")
@click.option(
    "--spatialite_mod",
    help="Path to SpatiaLite module, for if --spatialite cannot find it automatically",
)
def cli(db_path, table, geojson, pk, alter, spatialite, spatialite_mod):
    "Import GeoJSON into a SQLite database" ""
    data = json.load(geojson)
    if not isinstance(data, dict):
        raise click.ClickException("GeoJSON root must be an object")
    geojson_type = data.get("type")
    if geojson_type not in ("Feature", "FeatureCollection"):
        raise click.ClickException("GeoJSON must be a Feature or a FeatureCollection")
    if geojson_type == "Feature":
        features = [data]
    else:
        features = data["features"]
    utils.import_features(
        db_path,
        table,
        features,
        pk=pk,
        alter=alter,
        spatialite=spatialite,
        spatialite_mod=spatialite_mod,
    )
