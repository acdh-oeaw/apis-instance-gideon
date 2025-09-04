import django_tables2 as tables
from apis_core.relations.tables import RelationsListTable


class PersonPlaceRelationsTable(RelationsListTable):
    class Meta(RelationsListTable.Meta):
        pass

    date = tables.Column()
