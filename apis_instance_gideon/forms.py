from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from apis_core.core.fields import ApisModelSelect2Multiple
from apis_core.generic.forms import GenericFilterSetForm


class PersonFilterSetForm(GenericFilterSetForm):
    """
    Override the default FilterSet form to be able
    to replace the widget for the `profession` lookup
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self.fields["profession"]._queryset.model)
        url = reverse("apis_core:generic:autocomplete", args=[ct])
        self.fields["profession"].widget = ApisModelSelect2Multiple(url)
        self.fields["profession"].widget.choices = self.fields["profession"].choices
