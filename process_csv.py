#!/usr/bin/env python3
# Lit un fichier CSV de permis de construire (base Sitadel) et enrichit / formatte les données
from csv import DictReader, DictWriter
import sys
import sqlite3
from collections import defaultdict, OrderedDict
import json
import requests
import traceback
from io import StringIO


GEO_SEARCH_URL="https://api-adresse.data.gouv.fr/search/csv/"

# Base de coordonneees des parcelles
COORDS_FILE = "data/coords.sqlite"
COORDS_CURSOR = sqlite3.connect(COORDS_FILE).cursor()

CACHE_FILE = "data/cache-addresse.sqlite"
CACHE_CONN = sqlite3.connect(CACHE_FILE)
CACHE_CURSOR = CACHE_CONN.cursor()

COMMUNE_FILE="data/communes.csv"
COMMUNE_COORDS_FILE = "data/communes-coords.csv"

TYPE_EVT={
    1: "depot",
    2: "autorisation",
    3: "travaux"}

TYPE_NAT={
    1: "nouveau",
    2: "existant",
    3: "nouveau_sur_existant"
}

TYPE_OPERATION={
    1 : "no_surf",
    2 : "demolition",
    3 : "demolitions",
    4 : "agrandissement",
    5 : "const_log_indiv",
    6 : "const_log_resid",
    7 : "autre_logements",
    8 : "autre_locaux",
    9 : "log_vers_loc",
    10 : "loc_vers_log",
    11 : "transf_locaux",
    12 : "autre_logement",
    13 : "autre_locaux",
    14 : "autre"}

SURF_COEF={
    'A':0, # Surface existante avant travaux
    'B':1, # Surface en plus
    'D':1, # Surface en plus
    'E':-1, # Surface en moins
    'F':-1, # Surface en moins
}

SURF_TYPE={
    1:"logement",
    2:"hotel",
    3:"bureau",
    4:"commerce",
    5:"artisan",
    6:"industrie",
    7:"agricole",
    8:"entrepot",
    9: "public"}

currFilename= ""
currLine=0

def eprint(*args, **kwargs):
    print("%s:%d: " % (currFilename, currLine), file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)

# Fetch coords from addresses
def adresses_coords(addresses) :
    res = dict()
    queries = []
    for item in addresses :

        key = item['insee'] + ':' + item['address']

        # Look in cache
        cached = CACHE_CURSOR.execute("SELECT json from cache where id =?", (key,)).fetchone()
        if cached is not None:
            cached = json.loads(cached[0])
            cached['id'] = item['id']
            res[item['id']] = cached
        else:
            queries.append(item)

    # Query HTTP service only if necessary
    if len(queries) > 0 :

        # Prepare CSV input
        csvdata = StringIO()
        writer = DictWriter(csvdata, fieldnames=['id', 'address', 'insee'])
        writer.writeheader()
        for item in queries :
            writer.writerow(item)
        csvdata.seek(0)

        # query
        httpres = requests.post(GEO_SEARCH_URL,
                                data=dict(
                                    columns="address",
                                    citycode='insee'),
                                files=dict(data=csvdata))

        # Result
        reader = DictReader(StringIO(httpres.text), delimiter=",")
        for row in reader :
            # append to cache
            key = row['insee'] + ':' + row['address']
            CACHE_CURSOR.execute("INSERT OR REPLACE INTO cache(id, json) VALUES(?, ?)", (key, json.dumps(row)))
            res[row['id']] = row

        CACHE_CONN.commit()

    return res


# Load insee communes
communes = dict()
with open(COMMUNE_FILE) as f :
    csv = DictReader(f, delimiter=";")
    for row in csv :
        communes[row['Code_commune_INSEE']] = dict(
            cp=row['Code_postal'],
            nom=row['Nom_commune'])

# Coords of communes
with open(COMMUNE_COORDS_FILE) as f :
    csv = DictReader(f, delimiter=",")
    for row in csv :
        insee = row['insee']
        if insee in communes :
            commune = communes[insee]
            commune['lon'] = float(row['lon'])
            commune['lat'] = float(row['lat'])


def map_int(value, mapvals) :
    if value is None or value == "" :
        return None
    ivalue = int(value)
    return mapvals[ivalue]

# Parcelle id witout section
def to_parcelle_no_prefix(commune, cadastre) :

    if len(cadastre) == 6:
        section = cadastre[-2:].upper()
        parcelle = cadastre[:-2].upper()
    else:
        section = ''.join(list(filter(str.isalpha, cadastre)))
        parcelle = ''.join(list(filter(str.isdigit, cadastre)))
    if len(section) < 2:
        section = '0' + section
    while len(parcelle) < 4:
        parcelle = '0' + parcelle

    return commune + section + parcelle

def get_coords(parcelle_id) :
    COORDS_CURSOR.execute("SELECT x, y FROM coords where id_no_prefix = ?", (parcelle_id,))
    res = COORDS_CURSOR.fetchone()

    # more than one ?
    if COORDS_CURSOR.fetchone() :
        return None
    return res

def parseint(val) :
    if val is None or val == '':
        return None
    return int(val)

def parsefloat(val) :
    if val is None or val == '':
        return None
    return float(val)

def process_line(row) :

    commune_insee = row['COMM']
    (lat, lon) = (None, None)

    cadastres = list([row["CADASTRE%d" % i] for i in range(1, 4) if row["CADASTRE%d" % i]])
    parcelle_ids = list(map(lambda cadastre :  to_parcelle_no_prefix(commune_insee, cadastre),  cadastres))
    for parcelle_no_prefix in parcelle_ids :
        coords = get_coords(parcelle_no_prefix)
        if coords :
            (lon,lat)= coords
            break

    commune = communes[commune_insee] if commune_insee in communes else None

    adresse = ""
    for champ in ['NUM', 'TYPEVOIE', 'LIBELLEVOIE', 'LIEUDIT'] :
        adresse += " " + row['ADR_%s_T' % champ]
    adresse = adresse.strip()


    cadastres = []
    for i in range(1, 4) :
        cad = row["CADASTRE%d" % i]
        if cad :
            cadastres.append(cad)

    # Surfaces
    surf = defaultdict(lambda : 0)
    for key in row.keys() :
        if key.startswith("SDP_") :
            cleankey = key.replace(" ", "")
            val = row[key]
            if val is not None and val != "":
                val = int(val)
                if val != 0 :

                    # Type de surface 1 à 9 : SURF_TYPE
                    type=int(cleankey[5])

                    # A B D E or F
                    coef = SURF_COEF[cleankey[4]]
                    surf[type] += coef * val

    maxsurfval = None

    for surfidx, surfval in surf.items() :
        if surfval == 0 :
            continue
        if maxsurfval is None or surfval > maxsurfval :
            maxsurfval = surfval

    if maxsurfval is None :
        eprint("No max surf found for ", row['ID_PC'], dict(surf))

    maintype = None
    if len(surf) > 0 :
        maintype = next(iter(surf.keys()))

    # pas de colonne de surfce de locaux => logement
    if maintype is None and not "SDP_A2" in row :
        maintype = 1
            
    def getval(col) :
        if col in row :
            return row[col]
        else : 
            return None

    moa = parseint(getval('CAT_MOA'))

    if moa == 8 :
        moa = 80
    elif moa == 9 :
        moa = 90

    location = {
        "lon": parsefloat(lon),
        "lat": parsefloat(lat)}

    commune_nom = commune['nom'] if commune is not None else row['ADR_LOCALITE_T']
    commune_cp = commune['cp'] if commune is not None else row['ADR_CP_T']

    if lat is None:
        eprint(
            "Loc not found. Cadastres: ", cadastres,
            "parcelles:", parcelle_ids,
            "commune : %s : %s" % (commune_insee, commune_nom),
            "adresse:", adresse)

    nom_demandeur = getval('DENOMINATION_D')
    if getval('RS_D') :
        nom_demandeur = getval('RS_D')  + " " + nom_demandeur
    nom_demandeur = nom_demandeur.strip()
    id = getval('ID_PC')

    nom = nom_demandeur or id

    return OrderedDict(
        _id=id,

        nom=nom,

        commune_insee=commune_insee,
        commune= "%s - %s" % (commune_nom, commune_cp),

        annee=parseint(getval('ANNEE_DEPOT')),
        id_permis=id,

        maitre_ouvrage=str(moa),
        nom_demandeur=nom_demandeur,
        siret=getval('SIRET_D'),

        location=location,
        cadastres="; ".join(cadastres),
        adresse=adresse,
        loc_approx=False,

        superficie_terrain=parseint(getval('SUPERFICIE_T')),
        superficie_locaux=parseint(maxsurfval),

        niveaux=parseint(getval('NB_NIV_MAX')),

        evenement=map_int(getval('TYPE_EVT'), TYPE_EVT),
        type=map_int(maintype, SURF_TYPE),
        nature=map_int(getval('NATURE_PROJET'), TYPE_NAT),
        operation=map_int(getval('TYPE_OPERATION_CONSTR'), TYPE_OPERATION),

        date_reception=getval('DPC'),
        date_decision=getval('DATEREELLE_DECISION_FAV'),
        date_chantier=getval('DATEREELLE_DOC'))

def writejson(row) :
    json.dump(row, sys.stdout, indent=4)

# Accumulate / update permis
permis_dict = dict()
for filename in sys.argv[1:] :
    currFilename=filename

    with open(filename) as file :
        csv = DictReader(file)

        for i, row in enumerate(csv) :
            currLine=i
            try:
                permis = process_line(row)
                id = permis["id_permis"]
                permis_dict[id] = permis

            except Exception as e :
                eprint(e)
                traceback.print_exc(file=sys.stderr)

# Gather missing adresses
addresses = []
for key, permis in permis_dict.items() :
    if permis['location']['lat'] is None :
        addr = permis['adresse'].strip()
        if len(addr) > 0 :
            addresses.append(dict(
                id=key,
                insee=permis['commune_insee'],
                address=addr))

# Get coords from addresses (REST service)
coords = adresses_coords(addresses)
for id, res in coords.items() :
    score = parsefloat(res['result_score'])
    if score is not None and score > 0.5 :
        permis_dict[id]['location']['lon'] = parsefloat(res['longitude'])
        permis_dict[id]['location']['lat'] = parsefloat(res['latitude'])


# Still no coord ? Use the one of the city
for id, permis in permis_dict.items() :
    if permis['location']['lon'] is None :
        permis["loc_approx"] = True
        insee = permis["commune_insee"]
        if insee in communes :
            commune = communes[insee]
            if 'lon' in commune :
                permis['location']['lon'] = commune['lon']
                permis['location']['lat'] = commune['lat']

# Dump in output
sys.stdout.write("[")
first = True
for key, permis in permis_dict.items() :
    if first:
        first = False
    else:
        sys.stdout.write(",")
    writejson(permis)
sys.stdout.write("]")





