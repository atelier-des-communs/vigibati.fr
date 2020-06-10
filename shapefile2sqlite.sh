#!/usr/bin/env bash
# Commandes pour télécharger les shapefile du site du gouvernement et extraire les cendroides de chaque parcelle dans un fichier sqlite
DEP=$1
OUT=cadastre.sqlite
FILENAME=cadastre-$DEP-parcelles-shp.zip
SRS=EPSG:4326
TABLE=parcelles

# Download parcelle from the net
wget https://cadastre.data.gouv.fr/data/etalab-cadastre/2019-07-01/shp/departements/$DEP/$FILENAME
unzip $FILENAME

# Output only Id and centroid to sqlite DB
ogr2ogr -append -f SQLite -sql "SELECT ST_Centroid(geometry), id FROM parcelles" -dialect sqlite $OUT parcelles.shp -t_srs $SRS -nln $TABLE

rm $FILENAME
rm parcelles.*