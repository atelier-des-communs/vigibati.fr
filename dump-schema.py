#! /usr/bin/python3
from collections import OrderedDict
from json import dump
import sys


class Attribute :
    def __init__(self, name, label, type, display="summary", isname=False, **others) :
        self.name = name
        self.label = label
        self.type = type
        self.display = display
        self.isname = isname
        self.others = others


attributes=[

    Attribute("commune_insee", "Commune (INSEE)", "text", "hidden"),
    Attribute("commune", "Commune", "text", geofilter=True),

    Attribute("type", "type locaux", "enum"),
    Attribute("superficie_locaux", "superficie locaux", "number"),
    Attribute("niveaux", "étages", "number"),

    Attribute("nom", "Nom", "text", "summary", True),

    Attribute("annee", "Année", "number"),
    Attribute("id_permis", "N° Permis", "text", "details"),

    Attribute("maitre_ouvrage", "Maître d'ouvrage", "enum", "details"),
    Attribute("nom_demandeur", "Nom demandeur", "text", "summary"),
    Attribute("siret", "SIRET", "text", "details"),

    Attribute("location", "emplacement", "location", "hidden"),
    Attribute("adresse", "adresse", "text"),
    Attribute("cadastres", "cadastres", "text", "details"),
    Attribute("loc_approx", "lieu approximatif", "boolean", "hidden"),

    Attribute("superficie_terrain", "superficie terrain", "number", "details"),


    Attribute("evenement", "état du dossier", "enum"),

    Attribute("nature", "nature travaux", "enum"),
    Attribute("operation", "opération", "enum", "details"),

    Attribute("date_reception", "date de réception", "text", "details"),
    Attribute("date_decision", "date de décision", "text", "details"),
    Attribute("date_chantier", "date de chantier", "text", "details")]


enums = dict()

enums["evenement"] = [
    ("depot", "dépot"),
    ("autorisation", "autorisation"),
    ("travaux", "travaux")
]

enums["nature"] = [
    ("nouveau", "nouveau", "red"),
    ("existant", "existant", "green"),
    ("nouveau_sur_existant", "nouveau sur existant", "orange")
]

enums["operation"] = [
    ("no_surf", "Pas de surface"),
    ("demolition", "Démolition simple"),
    ("demolitions", "Démolitions multiples"),
    ("agrandissement", "Agrandissement de logement existant"),
    ("const_log_indiv", "Construction pure d'une maison individuelle"),
    ("const_log_resid", "Construction pure de logements en résidences"),
    ("autre_logements", "Autre construction pure de logements"),
    ("autre_locaux", "Construction pure de locaux"),
    ("log_vers_loc", "Transformation de logements en locaux"),
    ("loc_vers_log", "Transformation de locaux en logements"),
    ("transf_locaux", "Transformation de locaux"),
    ("autre_logement", "Autres opérations ne portant que sur de l'habitation"),
    ("autre_locaux", "Autres opérations ne portant que sur des locaux"),
    ("autre", "Autres opérations de construction")]

enums["type"] = [
    ("logement", "logement", "#488EF9"),
    ("hotel", "hotel", "#F9A148"),
    ("bureau", "bureau", "#F5F948"),
    ("commerce", "commerce", "#F94848"),
    ("artisan", "artisan", "#3c90c5"),
    ("industrie", "industrie", "#9E7430"),
    ("agricole", "agricole", "#34ab54"),
    ("entrepot", "entrepot", "#CECECE"),
    ("public", "public", "#3A9998")]

enums["maitre_ouvrage"] = [
    ("10", "Particuliers (SAI)"),
    ("11", "Particuliers purs"),
    ("12", "SCI de particuliers"),
    ("20", "Bailleurs sociaux SAI"),
    ("21", "Organismes HLM"),
    ("22", "EPL (ex SEM)"),
    ("23", "Autres organismes"),
    ("30", "Promoteurs (SAI)"),
    ("31", "Promoteurs reconnus"),
    ("32", "SCI ou autres"),
    ("33", "Autres professionnels"),
    ("40", "Administrations publiques (SAI)"),
    ("41", "État"),
    ("42", "Départements et régions"),
    ("43", "Communes"),
    ("50", "Autres sociétés"),
    ("80", "Sans objet (locaux purs)"),
    ("90", "Non déterminé"),
    ("1", "Maîtrise d'ouvrage Privée"),
    ("2", "Maîtrise d'ouvrage Publique")]

attrs = []
for attr in attributes :


    display = {
        "hidden" : dict(details=False, summary=False),
        "details" : dict(details=True, summary=False),
        "summary" : dict(details=True, summary=True)}[attr.display]

    outattr = dict(
        uid=attr.name,
        isName=attr.isname,
        isMandatory=False,
        system=False,
        display=display,
        name=attr.name,
        label=attr.label,
        type=dict(
            tag=attr.type,
        )
    )
    if attr.type == "text" :
        outattr['type']['rich'] = False
    if attr.type == "enum" :
        enumvals = enums[attr.name]

        def toenumvalue(item) :
            res = dict(
                value=item[0],
                label=item[1])
            if len(item) == 3 :
                res["color"] = item[2]
            return res

        outattr['type']['values'] = list(map(toenumvalue, enumvals))

    outattr.update(attr.others)

    attrs.append(outattr)

dump(attrs, sys.stdout, indent=4)
