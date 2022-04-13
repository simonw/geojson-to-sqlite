import click
import sqlite_utils
import json
from . import utils

import pdb


@click.command()
@click.version_option()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("table", required=True)
@click.argument("geojson", type=click.File(), required=True, nargs=-1)
@click.option("--nl", is_flag=True, help="Use newline-delimited GeoJSON features")
@click.option("--pk", help="Column to use as a primary key")
@click.option("--alter", is_flag=True, help="Add any missing columns")
@click.option(
    "--properties",
    is_flag=False,
    flag_value="properties",
    default="",
    help="Bundle properties into a JSON object called 'properties' or a custom name",
)
@click.option("--spatialite", is_flag=True, help="Use SpatiaLite")
@click.option("--spatial-index", is_flag=True, help="Create spatial indexes")
@click.option(
    "--spatialite_mod",
    help="Path to SpatiaLite module, for if --spatialite cannot find it automatically",
)
def cli(
    db_path,
    table,
    geojson,
    nl,
    pk,
    alter,
    properties,
    spatialite,
    spatial_index,
    spatialite_mod,
):
    """
    Import GeoJSON into a SQLite database

    To insert cities.geojson into a cities table in my.db:

        geojson-to-sqlite my.db cities cities.geojson

    This command can be passed more than one GeoJSON file
    """
    for file in geojson:
        try:
            features = utils.get_features(file, nl)
            utils.import_features(
                db_path,
                table,
                features,
                pk=pk,
                alter=alter,
                properties=properties,
                spatialite=spatialite,
                spatialite_mod=spatialite_mod,
                spatial_index=spatial_index,
            )
        except (TypeError, ValueError) as e:
            raise click.ClickException(str(e))
