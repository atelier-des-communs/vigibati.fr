#!/bin/bash

URL=https://vigibati.fr/api/vigibati/create
PENDING=data/pending
PROCESSED=data/processed

# Set password
source .env

for file in $PENDING/*.json; do
  echo posting "$file"
  http post $URL Cookie:wl_secret_vigibati=$SECRET < $file || continue

  root=${file%.*}
  mv $root.* $PROCESSED
done