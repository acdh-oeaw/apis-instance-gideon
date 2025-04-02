from django.db import models
from apis_core.apis_entities.abc import E53_Place, E21_Person, SimpleLabelModel
from apis_core.history.models import VersionMixin
from apis_core.generic.abc import GenericModel
from django.utils.translation import gettext_lazy as _
from apis_core.relations import abc as rel_abc


class ProfessionCategory(GenericModel, SimpleLabelModel):
    class Meta:
        verbose_name = _("Profession Category")
        verbose_name_plural = _("Profession Categories")


class Profession(GenericModel, SimpleLabelModel):
    class Meta:
        verbose_name = _("Profession")
        verbose_name_plural = _("Professions")


class Person(VersionMixin, E21_Person):
    d_biographien_id = models.IntegerField(editable=False)
    # domain
    domain = models.CharField(null=True)
    # vorname = forename
    # nachname = surname
    # weitere_namensformen
    alternative_names = models.TextField(null=True)
    # k_geschlecht = gender
    # adelspraedikat
    title = models.CharField(null=True)
    # ist_adelig
    aristocratical = models.CharField(null=True)
    # k_religion_id
    religion = models.CharField(null=True)
    # religion_anmerkung
    religion_comment = models.CharField(null=True)
    # religion_wechsel
    religion_change = models.IntegerField(null=True)
    # k_orden_id
    order = models.CharField(null=True)
    # k_berufsgruppen_id
    professioncategory = models.ForeignKey(ProfessionCategory, on_delete=models.CASCADE, null=True, blank=True)
    # beruf
    profession = models.ManyToManyField(Profession, blank=True)
    # geburtstagmonat, geburtsjahr, geburtsort_alt, geburtsort_heute, k_land_id_geburt_alt, k_land_id_geburt_heute
    # geburt_anmerkung, geburtsdaten_ok
    # sterbetagmonat, sterbejahr, sterbeort_alt, sterbeort_heute, k_land_id_tod_alt, k_land_id_tod_heute,
    # sterbe_anmerkung, sterbedaten_ok


class Place(E53_Place):
    ...


class BornIn(rel_abc.BornIn):
    subj_model = Person
    obj_model = Place


class DiedIn(rel_abc.DiedIn):
    subj_model = Person
    obj_model = Place
