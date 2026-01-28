import csv
from django.core.management.base import BaseCommand
from recommendations.models import Dealer

class Command(BaseCommand):
    help = "Import dealers from a CSV file (headers: name,type,address,city,province,country,latitude,longitude,contact_name,contact_phone,contact_email,inventory_tags)"

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to dealers CSV')

    def handle(self, *args, **options):
        path = options['csvfile']
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            created = 0
            for row in reader:
                Dealer.objects.update_or_create(
                    name=row.get('name','').strip(),
                    defaults={
                        'type': row.get('type','agrodealer').strip(),
                        'address': row.get('address','').strip(),
                        'city': row.get('city','').strip(),
                        'province': row.get('province','').strip(),
                        'country': row.get('country','').strip(),
                        'latitude': float(row.get('latitude')) if row.get('latitude') else None,
                        'longitude': float(row.get('longitude')) if row.get('longitude') else None,
                        'contact_name': row.get('contact_name','').strip(),
                        'contact_phone': row.get('contact_phone','').strip(),
                        'contact_email': row.get('contact_email','').strip(),
                        'inventory_tags': row.get('inventory_tags','').strip(),
                    }
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported/updated {created} dealers from {path}"))
