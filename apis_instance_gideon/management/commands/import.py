from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from collections import defaultdict
import csv
import json
import pathlib
from apis_instance_gideon.models import Person, Place, Profession, ProfessionCategory, BornIn, DiedIn, Corrigendum, PersonCorrigendum, Publication, PersonPublication, Quote, PersonQuote
from apis_core.collections.models import SkosCollection
from apis_core.uris.models import Uri

place_cache = {}


def create_born_in(p, row):
    placelabel = row["GEBURTSORT_HEUTE"]
    if placelabel == "?":
        placelabel = row.get("GEBURTSORT_ALT", "?")
    if placelabel not in place_cache:
        place_cache[placelabel], _ = Place.objects.get_or_create(label=placelabel)
    place = place_cache[placelabel]
    date = row["GEBURTSTAG_TEXT"]
    comment = row["GEBURT_ANMERKUNG"]
    data_ok = True if row["GEBURTSDATEN_OK"] == "-1" else False
    comment_date = row["ANMERKUNG_GEBURTSDATUM"]
    comment_place = row["ANMERKUNG_GEBURTSORT"]
    BornIn.objects.get_or_create(subj_content_type=p.content_type,
                                 subj_object_id=p.id,
                                 obj_content_type=place.content_type,
                                 obj_object_id=place.id,
                                 date=date,
                                 comment=comment,
                                 data_ok=data_ok,
                                 comment_date=comment_date,
                                 comment_place=comment_place)


def create_died_in(p, row):
    placelabel = row["STERBEORT_HEUTE"]
    if placelabel == "?":
        placelabel = row.get("STERBEORT_ALT", "?")
    if placelabel not in place_cache:
        place_cache[placelabel], _ = Place.objects.get_or_create(label=placelabel)
    place = place_cache[placelabel]
    date = row["STERBETAG_TEXT"]
    comment = row["STERBE_ANMERKUNG"]
    data_ok = True if row["STERBEDATEN_OK"] == "-1" else False
    comment_date = row["ANMERKUNG_STERBEDATUM"]
    comment_place = row["ANMERKUNG_STERBEORT"]
    DiedIn.objects.get_or_create(subj_content_type=p.content_type,
                                 subj_object_id=p.id,
                                 obj_content_type=place.content_type,
                                 obj_object_id=place.id,
                                 date=date,
                                 comment=comment,
                                 data_ok=data_ok,
                                 comment_date=comment_date,
                                 comment_place=comment_place)


def read_csv_to_dict(filename):
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


fieldmapping = {
        "forename": "VORNAME",
        "surname": "NACHNAME",
        "title": "ADELSPRAEDIKAT",
        "religion_comment": "RELIGION_ANMERKUNG",
        "kinfolk": "VERWANDSCHAFT",
        "education": "AUSBILDUNG",
        "career_path": "BERUF_LAUFBAHN",
        "life_center": "GEOGRAPH_LEBENSMITTELPUNKT",
        "special_accomplishments": "BESONDERE_LEISTUNGEN",
        "characteristics": "PERS_EIGENSCHAFTEN",
        "honours": "EHRUNGEN",
        "appreciations": "WUERDIGUNGEN",
        "works": "WERKSANGABEN",
        "archives": "ARCHIVALIEN",
        "notes": "MITTEILUNGEN",
        "corrigenda": "CORRIGENDA",
        "corrigenda_source": "CORRIGENDA_HERKUNFT",
        "curriculum_vitae": "LEBENSLAUF",
        "generic_comment": "ALLGEMEINE_ANMERKUNG",
        "comment_person": "ANMERKUNG_PERSON",
        "comment_religion": "ANMERKUNG_RELIGION",
        "comment_work": "ANMERKUNG_BERUF",
        "comment_kinfolk": "ANMERKUNG_VERWANDTSCHAFT",
        "literature": "LITERATURANGABEN",
}

copy_id_mapping = {}


def parse_d_biografien(filename):
    print(f"parse {filename}")
    parent = filename.parent
    person_content_type = ContentType.objects.get_for_model(Person)

    religionen = {}
    for row in read_csv_to_dict(parent / "K_RELIGIONEN.csv"):
        religionen[int(row["ID"])] = row["TITEL"]

    orders = {}
    for row in read_csv_to_dict(parent / "K_ORDEN.csv"):
        orders[int(row["ID"])] = row["TITEL"]

    professioncategories = {}
    for row in read_csv_to_dict(parent / "K_BERUFSGRUPPEN.csv"):
        professioncategories[int(row["ID"])] = row["TITEL"]

    domains = {}
    for row in read_csv_to_dict(parent / "DOMAINS.csv"):
        domain, _ = SkosCollection.objects.get_or_create(name=row["NAME"])
        domains[int(row["ID"])] = domain

    weitere_namen = defaultdict(list)
    for row in read_csv_to_dict(parent / "BIOGRAFIEN_WEITERE_NAMEN.csv"):
        name = row["VORNAME"] + " " + row["NACHNAME"]
        weitere_namen[int(row["BIOGRAFIE_ID"])].append(name.strip())

    links = defaultdict(list)
    for row in read_csv_to_dict(parent / "BIOGRAFIEN_LINKS.csv"):
        links[int(row["D_BIOGRAPHIEN_ID"])].append(row["LINK"])

    ng_comments = defaultdict(list)
    for row in read_csv_to_dict(parent / "NG_COMMENTS.csv"):
        comment = row["FIELD"] + ":" + row["KOMMENTAR"]
        ng_comments[int(row["DSID"])].append(comment)

    profession_mapping = {}
    professioncategory_cache = {}
    db_persons = []
    biographien = {}
    urimapping = []
    print("Read biographies ...")
    for row in read_csv_to_dict(filename):
        if not row["D_BIOGRAFIEN_ORIGINAL_ID"]:
            biographien[int(row["ID"])] = row

    # we overwrite the 64 entries that have copies
    print("Overwrite copies ...")
    for row in read_csv_to_dict(filename):
        if row["D_BIOGRAFIEN_ORIGINAL_ID"]:
            copy_id_mapping[int(row["ID"])] = int(row["D_BIOGRAFIEN_ORIGINAL_ID"])
            biographien[int(row["D_BIOGRAFIEN_ORIGINAL_ID"])] = row

    for old_id, row in biographien.items():
        p, _ = Person.objects.get_or_create(old_id=old_id)
        for attribute, fieldname in fieldmapping.items():
            setattr(p, "attribute", row[fieldname])
        p.alternative_names = row["WEITERE_NAMENSFORMEN"].split() + weitere_namen.get(old_id, [])
        p.gender = "male" if row["K_GESCHLECHT_ID"] == 1 else "female"
        p.aristocratical = True if row["IST_ADELIG"] == -1 else False
        p.religion = religionen[int(row["K_RELIGIONEN_ID"])]
        p.religion_change = True if row["RELIGIONSWECHSEL"] == -1 else False
        p.order = orders[int(row["K_ORDEN_ID"])] if row["K_ORDEN_ID"] else None
        p.links = links.get(old_id, [])
        db_persons.append(p)
        if berufsgruppen_id := row["K_BERUFSGRUPPEN_ID"]:
            label = professioncategories[int(berufsgruppen_id)]
            if label not in professioncategory_cache.keys():
                professioncategory_cache[label], _ = ProfessionCategory.objects.get_or_create(label=label)
            p.professioncategory = professioncategory_cache[label]
        if beruf := row["BERUF"]:
            profession_mapping[old_id] = beruf
        domains[int(row["DOMAIN"])].add(p)
        create_born_in(p, row)
        create_died_in(p, row)
        print(f"{old_id}: {p}")
        if row["PNDID"]:
            urimapping.append((row["PNDID"], person_content_type, p.id))
        fields = list(fieldmapping.keys()) + ["professioncategory", "alternative_names", "gender", "aristocratical", "religion", "religion_change", "order", "links"]
        if len(db_persons) > 1000:
            print("writing persons ...")
            Person.objects.bulk_update(db_persons, fields)
            db_persons.clear()

    print("mapping professions ...")
    profession_cache = {}
    for person_id, label in profession_mapping.items():
        if label not in profession_cache.keys():
            profession_cache[label], _ = Profession.objects.get_or_create(label=label)
        p = Person.objects.get(old_id=person_id)
        p.profession.add(profession_cache[label])

    print("creating uris ...")
    for (pnd, content_type, object_id) in urimapping:
        try:
            Uri.objects.get_or_create(uri=f"https://d-nb.info/gnd/{pnd}", content_type=content_type, object_id=object_id)
        except Exception as e:
            print(f"GND Uri {pnd} on content_type {content_type} / object_id {object_id} can not be created: {e}")


def parse_biografie_literatur(filename):
    all_attachments = defaultdict(list)
    for row in read_csv_to_dict(filename.parent / "NG_ATTACHMENTS.csv"):
        attachment = row["ID"] + row["ATTACHMENT_TYPE"]
        all_attachments[int(row["DSID"])].append(attachment)
    for row in read_csv_to_dict(filename):
        p_id = int(row["BIOGRAFIE_ID"])
        if p_id in copy_id_mapping.keys():
            p_id = copy_id_mapping[p_id]
        try:
            p = Person.objects.get(old_id=p_id)
            attachments = all_attachments.get(p_id, [])
            q, _ = Quote.objects.get_or_create(old_id=row["ID"], quotation=row["ZITAT"], quotation_shortform=row["KURZFORM"], attachments=attachments)
            pq, _ = PersonQuote.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=q.content_type, obj_object_id=q.id)
        except Person.DoesNotExist:
            print(f"Biographien ID: {p_id} does not exist")


def parse_biografien_corrigenda(filename):
    kategorien = {}
    for row in read_csv_to_dict(filename.parent / "K_CORRIGENDA_KATEGORIEN.csv"):
        kategorien[int(row["ID"])] = row["TITEL"]
    for row in read_csv_to_dict(filename):
        p_id = int(row["BIOGRAFIE_ID"])
        if p_id in copy_id_mapping.keys():
            p_id = copy_id_mapping[p_id]
        try:
            p = Person.objects.get(old_id=p_id)
            old_id = row["ID"]
            data_old = row["DATEN_ALT"]
            data_new = row["DATEN_NEU"]
            review_by = row["UEBERPRUEFUNG"]
            source = row["QUELLE"]
            category = kategorien[int(row["K_CORRIGENDA_KATEGORIEN_ID"])]
            c, _ = Corrigendum.objects.get_or_create(old_id=old_id, data_old=data_old, data_new=data_new, review_by=review_by, source=source, category=category)
            pc, _ = PersonCorrigendum.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=c.content_type, obj_object_id=c.id)
        except Person.DoesNotExist:
            print(f"Biographien ID: {p_id} does not exist")


def parse_biografien_publikationen(filename):
    for i, row in enumerate(read_csv_to_dict(filename)):
        print(f"{i}: {filename}")
        p_id = int(row["BIOGRAFIE_ID"])
        if p_id in copy_id_mapping.keys():
            p_id = copy_id_mapping[p_id]
        try:
            p = Person.objects.get(old_id=p_id)
            old_id = row["ID"]
            volume = int(row["BAND_VC"]) if row["BAND_VC"] != "" else None
            delivery = int(row["LIEFERUNG_VC"]) if row["LIEFERUNG_VC"] != "" else None
            page_bio = row["SEITE_BIO"]
            page_number = row["SEITENANGABEN"]
            mentioned = int(row["MITERWAEHNT"]) if row["MITERWAEHNT"] != "" else None
            pu, _ = Publication.objects.get_or_create(old_id=old_id, volume=volume, delivery=delivery, page_bio=page_bio, page_number=page_number, mentioned=mentioned)
            pp, _ = PersonPublication.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=pu.content_type, obj_object_id=pu.id)
        except Person.DoesNotExist:
            print(f"Biographien ID: {p_id} does not exist")


class Command(BaseCommand):
    help = "Import data from MongoDB Export"

    def add_arguments(self, parser):
        parser.add_argument("file", type=pathlib.Path)

    def handle(self, *args, **options):
        parse_d_biografien(options["file"] / "D_BIOGRAFIEN_DOMAINS_1457.csv")
        parse_biografien_publikationen(options["file"] / "BIOGRAFIEN_PUBLIKATIONEN.csv")
        parse_biografien_corrigenda(options["file"] / "BIOGRAFIEN_CORRIGENDA.csv")
        parse_biografie_literatur(options["file"] / "BIOGRAFIE_LITERATUR.csv")
