from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recommendations.models import Recommendation, Treatment, Dealer
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = "Seed a sample agronomist, one recommendation+ treatment, and optional sample dealers."

    def handle(self, *args, **options):
        # create agronomist user (if not exists)
        username = "agronomist"
        email = "agronomist@example.com"
        user, created = User.objects.get_or_create(username=username, defaults={'email':email})
        if created:
            user.set_password('password123')
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Created sample agronomist user (username=agronomist, password=password123)"))
        else:
            self.stdout.write("Agronomist user exists")

        # sample recommendation
        rec, rcreated = Recommendation.objects.get_or_create(
            disease_code='frogeye_spot',
            defaults={
                'title':'Frogeye leaf spot (sample)',
                'severity':'moderate',
                'nonchem_recommendations':'Remove severely affected leaves; improve air circulation.',
                'created_by':user,
                'approved_by':user,
                'approved_at':timezone.now(),
                'version':1,
                'published':True,
                'safety_flag':True,
            }
        )
        if rcreated:
            Treatment.objects.create(
                recommendation=rec,
                type='chemical',
                name='Azoxystrobin 250SC (sample)',
                active_ingredient='azoxystrobin',
                dose_text='Mix 50 ml per 10 L water, foliar spray to runoff. Repeat after 7-14 days if needed.',
                application_method='Foliar spray',
                pre_harvest_interval='14 days',
                ppe='Gloves, mask, goggles',
                source='TRB sample guidance 2025'
            )
            self.stdout.write(self.style.SUCCESS("Created sample recommendation 'frogeye_spot' and treatment."))

        # optional sample dealers if none exist
        if Dealer.objects.count() == 0:
            Dealer.objects.create(
                name="Kutsaga Agrovet",
                type="agrovet",
                city="Harare",
                province="Mashonaland East",
                country="Zimbabwe",
                latitude=-17.800,
                longitude=31.000,
                contact_name="John Doe",
                contact_phone="+263772000000",
                contact_email="kutsaga@example.com",
                inventory_tags="fungicide,azoxystrobin"
            )
            Dealer.objects.create(
                name="Borrowdale Veterinary Clinic",
                type="veterinary_clinic",
                city="Harare",
                province="Harare",
                country="Zimbabwe",
                latitude=-17.820,
                longitude=31.040,
                contact_name="Dr. Vet",
                contact_phone="+263772111111",
                contact_email="vet@example.com",
                inventory_tags=""
            )
            self.stdout.write(self.style.SUCCESS("Created 2 sample dealers."))

        self.stdout.write(self.style.SUCCESS("Phase1 seed complete."))
