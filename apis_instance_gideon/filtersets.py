from apis_core.apis_entities.filtersets import AbstractEntityFilterSet
from apis_instance_gideon.forms import PersonFilterSetForm


class PersonFilterSet(AbstractEntityFilterSet):
    """
    We override the default FilterSet to be able to set
    a custom form which overrides the `profession` lookup.
    """

    class Meta(AbstractEntityFilterSet.Meta):
        form = PersonFilterSetForm
