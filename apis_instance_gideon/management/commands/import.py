from django.core.management.base import BaseCommand
from collections import defaultdict
import csv
import json
import pathlib
from apis_instance_gideon.models import Person, Place, Profession, ProfessionCategory, BornIn, DiedIn, Corrigendum, PersonCorrigendum, Publication, PersonPublication, Quote, PersonQuote
from apis_core.collections.models import SkosCollection


def create_bd_rel(p, row):
    for bd in ["GEBURT", "STERBE"]:
        bd2 = "GEBURTS" if bd == "GEBURT" else "STERBE"
        place, _ = Place.objects.get_or_create(label=row[f"{bd2}ORT_HEUTE"])
        if place_old := row.get("{bd2}ORT_ALT", None):
            place.alternative_labels.append(place_old)
            place.save()
        date = row[f"{bd2}TAG_TEXT"]
        comment = row[f"{bd}_ANMERKUNG"]
        data_ok = True if row[f"{bd2}DATEN_OK"] == -1 else False
        comment_date = row[f"ANMERKUNG_{bd2}DATUM"]
        comment_place = row[f"ANMERKUNG_{bd2}ORT"]
        if bd == "GEBURT":
            rel, _ = BornIn.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=place.content_type, obj_object_id=place.id, date=date, comment=comment, data_ok=data_ok, comment_date=comment_date, comment_place=comment_place)
        if bd == "STERBE":
            rel, _ = DiedIn.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=place.content_type, obj_object_id=place.id, date=date, comment=comment, data_ok=data_ok, comment_date=comment_date, comment_place=comment_place)


doubles = defaultdict(list)


def lookupid(id: int) -> int:
    for key, values in doubles.items():
        if id in values:
            id = lookupid(int(key))
            break
    return id


def parse_d_biografien(filename):
    religionen = {}
    with open(filename.parent / "K_RELIGIONEN.csv") as relgionen_csv:
        for row in csv.DictReader(relgionen_csv):
            religionen[row["ID"]] = row["TITEL"]
    orders = {}
    with open(filename.parent / "K_ORDEN.csv") as orden_csv:
        for row in csv.DictReader(orden_csv):
            orders[row["ID"]] = row["TITEL"]
    professioncategories = {}
    with open(filename.parent / "K_BERUFSGRUPPEN.csv") as berufsgruppen_csv:
        for row in csv.DictReader(berufsgruppen_csv):
            professioncategories[row["ID"]] = row["TITEL"]
    domains = {}
    with open(filename.parent / "DOMAINS.csv") as domains_csv:
        for row in csv.DictReader(domains_csv):
            domain, _ = SkosCollection.objects.get_or_create(name=row["NAME"])
            domains[int(row["ID"])] = domain
    weitere_namen = defaultdict(list)
    with open(filename.parent / "BIOGRAFIEN_WEITERE_NAMEN.csv") as weitere_namen_csv:
        for row in csv.DictReader(weitere_namen_csv):
            name = row["VORNAME"] + " " + row["NACHNAME"]
            weitere_namen[row["BIOGRAFIE_ID"]].append(name.strip())
    links = defaultdict(list)
    with open(filename.parent / "BIOGRAFIEN_LINKS.csv") as links_csv:
        for row in csv.DictReader(links_csv):
            links[row["D_BIOGRAPHIEN_ID"]].append(row["LINK"])
    ng_comments = defaultdict(list)
    with open(filename.parent / "NG_COMMENTS.csv") as comments_csv:
        for row in csv.DictReader(comments_csv):
            comment = row["FIELD"] + ":" + row["KOMMENTAR"]
            ng_comments[row["DSID"]].append(comment)
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row["D_BIOGRAFIEN_ORIGINAL_ID"]:
                continue
                id_ = int(row["ID"])
                p, _ = Person.objects.get_or_create(old_id=id_)
                p.forename = row["VORNAME"]
                p.surname = row["NACHNAME"]
                p.alternative_names = row["WEITERE_NAMENSFORMEN"].split() + weitere_namen.get(row["ID"], [])
                p.gender = "male" if row["K_GESCHLECHT_ID"] == 1 else "female"
                p.title = row["ADELSPRAEDIKAT"]
                p.ist_adelig = True if row["IST_ADELIG"] == -1 else False
                p.religion = religionen[row["K_RELIGIONEN_ID"]]
                p.religion_comment = row["RELIGION_ANMERKUNG"]
                p.religion_change = True if row["RELIGIONSWECHSEL"] == -1 else False
                p.order = orders[row["K_ORDEN_ID"]] if row["K_ORDEN_ID"] else None
                p.kinfolk = row["VERWANDSCHAFT"]
                p.education = row["AUSBILDUNG"]
                p.career_path = row["BERUF_LAUFBAHN"]
                p.life_center = row["GEOGRAPH_LEBENSMITTELPUNKT"]
                p.special_accomplishments = row["BESONDERE_LEISTUNGEN"]
                p.characteristics = row["PERS_EIGENSCHAFTEN"]
                p.honours = row["EHRUNGEN"]
                p.appreciations = row["WUERDIGUNGEN"]
                p.works = row["WERKSANGABEN"]
                p.archives = row["ARCHIVALIEN"]
                p.notes = row["MITTEILUNGEN"]
                p.corrigenda = row["CORRIGENDA"]
                p.corrigenda_source = row["CORRIGENDA_HERKUNFT"]
                p.curriculum_vitae = row["LEBENSLAUF"]
                p.generic_comment = row["ALLGEMEINE_ANMERKUNG"]
                p.comment_person = row["ANMERKUNG_PERSON"]
                p.comment_religion = row["ANMERKUNG_RELIGION"]
                p.comment_work = row["ANMERKUNG_BERUF"]
                p.comment_kinfolk = row["ANMERKUNG_VERWANDTSCHAFT"]
                p.literature = row["LITERATURANGABEN"]
                p.links = links.get(row["ID"], [])
                if beruf := row["BERUF"]:
                    profession, _ = Profession.objects.get_or_create(label=beruf)
                    p.profession.add(profession)
                if berufsgruppen_id := row["K_BERUFSGRUPPEN_ID"]:
                    professioncategory, _ = ProfessionCategory.objects.get_or_create(label=professioncategories[berufsgruppen_id])
                    p.professioncategory = professioncategory
                p.save()
                domains[int(row["DOMAIN"])].add(p)
                create_bd_rel(p, row)
            else:
                original_id = int(row["D_BIOGRAFIEN_ORIGINAL_ID"])
                _id = int(row["ID"])
                doubles[original_id].append(_id)
    print(json.dumps(doubles))
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if original_id := row.get("D_BIOGRAFIEN_ORIGINAL_ID", None):
                id = lookupid(int(original_id))
                domain = domains[int(row["DOMAIN"])]
                try:
                    p = Person.objects.get(old_id=id)
                    domain.add(p)
                    print(f"Added {domain} to {p}")
                except Person.DoesNotExist:
                    print(f"Biographien ID: {id} does not exist")


def parse_biografie_literatur(filename):
    all_attachments = defaultdict(list)
    with open(filename.parent / "NG_ATTACHMENTS.csv") as attachments_csv:
        for row in csv.DictReader(attachments_csv):
            attachment = row["ID"] + row["ATTACHMENT_TYPE"]
            all_attachments[row["DSID"]].append(attachment)
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p_id = int(row["BIOGRAFIE_ID"])
            p_id = lookupid(p_id)
            try:
                p = Person.objects.get(old_id=p_id)
                attachments = all_attachments.get(row["BIOGRAFIE_ID"], [])
                q, _ = Quote.objects.get_or_create(old_id=row["ID"], quotation=row["ZITAT"], quotation_shortform=row["KURZFORM"], attachments=attachments)
                pq, _ = PersonQuote.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=q.content_type, obj_object_id=q.id)
            except Person.DoesNotExist:
                print(f"Biographien ID: {p_id} does not exist")


def parse_biografien_corrigenda(filename):
    kategorien = {}
    with open(filename.parent / "K_CORRIGENDA_KATEGORIEN.csv") as kategorien_csv:
        for row in csv.DictReader(kategorien_csv):
            kategorien[row["ID"]] = row["TITEL"]
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p_id = int(row["BIOGRAFIE_ID"])
            p_id = lookupid(p_id)
            try:
                p = Person.objects.get(old_id=p_id)
                old_id = row["ID"]
                data_old = row["DATEN_ALT"]
                data_new = row["DATEN_NEU"]
                review_by = row["UEBERPRUEFUNG"]
                source = row["QUELLE"]
                category = kategorien[row["K_CORRIGENDA_KATEGORIEN_ID"]]
                c, _ = Corrigendum.objects.get_or_create(old_id=old_id, data_old=data_old, data_new=data_new, review_by=review_by, source=source, category=category)
                pc, _ = PersonCorrigendum.objects.get_or_create(subj_content_type=p.content_type, subj_object_id=p.id, obj_content_type=c.content_type, obj_object_id=c.id)
            except Person.DoesNotExist:
                print(f"Biographien ID: {p_id} does not exist")


def parse_biografien_publikationen(filename):
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p_id = int(row["BIOGRAFIE_ID"])
            p_id = lookupid(p_id)
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
        parse_d_biografien(options["file"] / "D_BIOGRAFIEN.csv")
        parse_biografien_publikationen(options["file"] / "BIOGRAFIEN_PUBLIKATIONEN.csv")
