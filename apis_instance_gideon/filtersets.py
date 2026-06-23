from apis_core.entities.filtersets import EntityFilterSet
from apis_instance_gideon.forms import PersonFilterSetForm


class PersonFilterSet(EntityFilterSet):
    """
    We override the default FilterSet to be able to set
    a custom form which overrides the `profession` lookup.
    """

    class Meta(EntityFilterSet.Meta):
        form = PersonFilterSetForm
