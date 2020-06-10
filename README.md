# vigibati.fr
Ce repo contient des scripts de traitement de la base nationale Sitadel de permis de construire pour le site vigibati.fr

# Scripts

## main-scrap.py

> ./main-scrap.py

* Telecharge les fichier csv qui ne sont pas presents dans `data/processed`
* Transforme les fichiers CSV en fichiers json (appelle process_csv.py)


## process_csv.py

> process.py file.csv > file.json 2> file.err

Compter les postions approxmimatives :

> for i in pending/*.json; do echo $i `grep approx $i | grep true | wc -l`; done

Environ 5% normalement

## Post to wikilist / vigibati.fr

Avec [httpie](https://httpie.org/) :

> http post https://vigibati.fr/api/vigibati/create Cookie:wl_secret_vigibati=$SECRET < <file.json>


 

