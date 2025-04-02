from django.core.management.base import BaseCommand
import csv
import pathlib


def parse_d_biografien(filename):
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row["D_BIOGRAFIEN_ORIGINAL_ID"]:
                print(row)


class Command(BaseCommand):
    help = "Import data from MongoDB Export"

    def add_arguments(self, parser):
        parser.add_argument("file", type=pathlib.Path)

    def handle(self, *args, **options):
        for csv_file in options["file"].glob("*.csv"):
            method_name = f"parse_{csv_file.stem.lower()}"
            if method := globals().get(method_name, None):
                method(csv_file)
