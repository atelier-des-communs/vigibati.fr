# vigibati.fr

Ce repository contient des scripts de traitement de la base nationale Sitadel de permis de construire pour le site [https://vigibati.fr](https://vigibati.fr)


# Données préalables

Pour fonctionner plusieurs fichiers doivent être présents :
* `data/communes.csv` : à télécharger sur [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/base-officielle-des-codes-postaux/)
* `data/coords.sqlite` : un fichier transformé depuis la liste des parcelles récupérées via le script `shapefile2sqlite.sh`. Ce fichier est à [récupérer sur ce cloud](https://cloud.raphael-jolivet.name/nextcloud/index.php/s/d1MkPM1vexZdFZT)

# Scripts

## main-scrap.py

> ./main-scrap.py

* Telecharge les fichiers csv qui ne sont pas presents dans `data/processed`
* Transforme les fichiers CSV en fichiers json (appelle process_csv.py)

## process_csv.py (appelé par main-scrap.py)

> process_csv.py file.csv > file.json 2> file.err

Compter les "location" approximatives :

> for i in pending/*.json; do echo $i `grep approx $i | grep true | wc -l`; done

Environ 5% normalement

## Post to wikilist / vigibati.fr

Avec [httpie](https://httpie.org/) :

> http post https://vigibati.fr/api/vigibati/create Cookie:wl_secret_vigibati=$SECRET < <file.json>
