from django.db import models
from django.contrib.postgres.fields import ArrayField
from apis_core.apis_entities.abc import E53_Place, E21_Person, SimpleLabelModel
from apis_core.history.models import VersionMixin
from apis_core.generic.abc import GenericModel
from django.utils.translation import gettext_lazy as _
#from apis_core.relations import abc as rel_abc
from apis_core.relations.models import Relation
from apis_core.apis_entities.models import AbstractEntity
from django_interval.fields import FuzzyDateParserField


class ProfessionCategory(GenericModel, SimpleLabelModel):
    class Meta:
        verbose_name = _("Profession Category")
        verbose_name_plural = _("Profession Categories")


class Profession(GenericModel, SimpleLabelModel):
    class Meta:
        verbose_name = _("Profession")
        verbose_name_plural = _("Professions")


class Person(E21_Person, VersionMixin, AbstractEntity):
    _default_search_fields = ["forename", "surname"]
    old_id = models.IntegerField(editable=False)
    # VORNAME = forename
    # NACHNAME = surname
    birth_date = None
    death_date = None
    alternative_names = ArrayField(models.CharField(), null=True, help_text="WEITERE_NAMENSFORMEN")
    # K_GESCHLECHT = gender
    title = models.CharField(null=True, help_text="ADELSPRAEDIKAT")
    aristocratical = models.BooleanField(null=True, help_text="IST_ADELIG")
    religion = models.CharField(null=True, help_text="K_RELIGION_ID")
    religion_comment = models.CharField(null=True, help_text="RELIGION_ANMERKUNG")
    religion_change = models.BooleanField(null=True, help_text="RELIGIONSWECHSEL")
    order = models.CharField(null=True, help_text="K_ORDEN_ID")
    professioncategory = models.ForeignKey(ProfessionCategory, on_delete=models.CASCADE, null=True, blank=True, help_text="K_BERUFSGRUPPEN_ID")
    profession = models.ManyToManyField(Profession, blank=True, help_text="BERUF")
    kinfolk = models.TextField(null=True, help_text="VERWANDSCHAFT")
    education = models.TextField(null=True, help_text="AUSBILDUNG")
    career_path = models.TextField(null=True, help_text="BERUF_LAUFBAHN")
    life_center = models.TextField(null=True, help_text="GEOGRAPH_LEBENSMITTELPUNKT")
    special_accomplishments = models.TextField(null=True, help_text="BESONDERE_LEISTUNGEN")
    characteristics = models.TextField(null=True, help_text="PERS_EIGENSCHAFTEN")
    honours = models.TextField(null=True, help_text="EHRUNGEN")
    appreciations = models.TextField(null=True, help_text="WUERDIGUNGEN")
    works = models.TextField(null=True, help_text="WERKSANGABEN")
    archives = models.TextField(null=True, help_text="ARCHIVALIEN")
    notes = models.TextField(null=True, help_text="MITTEILUNGEN")
    corrigenda = models.TextField(null=True, help_text="CORRIGENDA")
    corrigenda_source = models.TextField(null=True, help_text="CORRIGENDA_HERKUNFT")
    curriculum_vitae = models.TextField(null=True, help_text="LEBENSLAUF")
    generic_comment = models.TextField(null=True, help_text="ALLGEMEINE_ANMERKUNG")
    comment_person = models.TextField(null=True, help_text="ANMERKUNG_PERSON")
    comment_religion = models.TextField(null=True, help_text="ANMERKUNG_RELIGION")
    comment_work = models.TextField(null=True, help_text="ANMERKUNG_BERUF")
    comment_kinfolk = models.TextField(null=True, help_text="ANMERKUNG_VERWANDTSCHAFT")
    literature = models.TextField(null=True, help_text="LITERATURANGABEN")
    links = ArrayField(models.CharField(), null=True, help_text="BIOGRAFIEN_LINKS")
    field_comments = ArrayField(models.CharField(), null=True, help_text="NG_COMMENTS")


class Place(E53_Place, AbstractEntity):
    alternative_labels = ArrayField(models.CharField(), null=True)


class Quote(GenericModel, models.Model):
    old_id = models.IntegerField(editable=False)
    quotation = models.CharField(null=True)
    quotation_shortform = models.CharField(null=True)
    attachments = ArrayField(models.CharField(), null=True, help_text="NG_ATTACHMENTS")

    def __str__(self):
        return self.quotation or ""


class Corrigendum(GenericModel, models.Model):
    old_id = models.IntegerField(editable=False)
    data_old = models.CharField(null=True)
    data_new = models.CharField(null=True)
    review_by = models.CharField(null=True)
    source = models.CharField()
    category = models.CharField()


class Publication(GenericModel, models.Model):
    old_id = models.IntegerField(editable=False)
    volume = models.IntegerField(null=True)
    delivery = models.IntegerField(null=True)
    page_bio = models.CharField(null=True)
    page_number = models.CharField(null=True)
    mentioned = models.IntegerField(null=True)

    def __str__(self):
        ret = f"Vol: {self.volume}"
        if self.delivery:
            ret += f", {self.delivery}"
        return ret


class BornIn(Relation):
    # GEBURTSTAGMONAT, GEBURTSJAHR, GEBURTSORT_ALT, GEBURTSORT_HEUTE, K_LAND_ID_GEBURT_ALT, K_LAND_ID_GEBURT_HEUTE
    # GEBURT_ANMERKUNG, GEBURTSDATEN_OK
    subj_model = Person
    obj_model = Place

    date = FuzzyDateParserField()
    comment = models.TextField()
    data_ok = models.BooleanField()
    comment_date = models.TextField()
    comment_place = models.TextField()


class DiedIn(Relation):
    # STERBETAGMONAT, STERBEJAHR, STERBEORT_ALT, STERBEORT_HEUTE, K_LAND_ID_TOD_ALT, K_LAND_ID_TOD_HEUTE,
    # STERBE_ANMERKUNG, STERBEDATEN_OK
    subj_model = Person
    obj_model = Place

    date = FuzzyDateParserField()
    comment = models.TextField()
    data_ok = models.BooleanField()
    comment_date = models.TextField()
    comment_place = models.TextField()


class PersonQuote(Relation):
    subj_model = Person
    obj_model = Quote


class PersonCorrigendum(Relation):
    subj_model = Person
    obj_model = Corrigendum


class PersonPublication(Relation):
    subj_model = Person
    obj_model = Publication
