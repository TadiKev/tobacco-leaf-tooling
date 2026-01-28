# recommendations/management/commands/seed_recommendations.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from recommendations.models import Recommendation, Treatment, Dealer

User = get_user_model()

SAMPLES = [
    {
        "disease_code": "alternaria",
        "title": "Alternaria leaf spot",
        "severity": "moderate",
        "nonchem_recommendations": "Remove and destroy infected leaves, improve airflow, crop rotation, and avoid overhead irrigation.",
        "treatments": [
            {
                "type": "chemical",
                "name": "Mancozeb 80WP",
                "active_ingredient": "mancozeb",
                "dose_text": "2–3 kg/ha as a spray (follow label).",
                "application_method": "Foliar spray",
                "pre_harvest_interval": "14 days",
                "ppe": "Gloves, mask, goggles",
                "notes": "Rotate modes of action. Apply with adequate water.",
                "source": "Sample guidance"
            },
        ],
    },
    {
        "disease_code": "cercospora",
        "title": "Cercospora leaf spot",
        "severity": "moderate",
        "nonchem_recommendations": "Improve drainage, remove crop debris, and avoid dense canopies. Use resistant varieties when available.",
        "treatments": [
            {
                "type": "chemical",
                "name": "Azoxystrobin 250 SC",
                "active_ingredient": "azoxystrobin",
                "dose_text": "50 ml / 10 L water (follow label directions).",
                "application_method": "Foliar spray",
                "pre_harvest_interval": "14 days",
                "ppe": "Gloves, mask",
                "notes": "Do not exceed recommended number of applications per season.",
                "source": "Sample guidance"
            }
        ],
    },
    {
        "disease_code": "healthy",
        "title": "Healthy crop — no treatment required",
        "severity": "mild",
        "nonchem_recommendations": "Plant appears healthy. Continue routine monitoring. Use good agronomic practices and scout weekly.",
        "treatments": []
    }
]

class Command(BaseCommand):
    help = "Seed published recommendations for alternaria, cercospora, healthy (creates agronomist user if missing)."

    def handle(self, *args, **options):
        username = "agronomist"
        email = "agronomist@example.com"
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password("password123")
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Created sample agronomist user (username=agronomist password=password123)"))
        else:
            self.stdout.write("Agronomist user exists")

        created_count = 0
        updated_count = 0

        for sample in SAMPLES:
            code = sample["disease_code"].lower().strip()
            rec, rec_created = Recommendation.objects.get_or_create(
                disease_code__iexact=code,
                defaults={
                    "disease_code": code,
                    "title": sample["title"],
                    "severity": sample.get("severity", "moderate"),
                    "nonchem_recommendations": sample.get("nonchem_recommendations", ""),
                    "created_by": user,
                    "approved_by": user,
                    "approved_at": timezone.now(),
                    "version": 1,
                    "published": True,
                    "safety_flag": False,
                }
            )

            # If get_or_create with disease_code__iexact didn't work (older Django versions), fallback:
            if rec_created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created recommendation for '{code}'"))
            else:
                # update fields and mark published = True (idempotent)
                rec.title = sample["title"]
                rec.severity = sample.get("severity", rec.severity)
                rec.nonchem_recommendations = sample.get("nonchem_recommendations", rec.nonchem_recommendations)
                rec.created_by = rec.created_by or user
                rec.approved_by = user
                rec.approved_at = timezone.now()
                rec.version = max(rec.version or 1, 1)
                rec.published = True
                rec.safety_flag = rec.safety_flag or False
                rec.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated recommendation for '{code}' (published=True)"))

            # ensure treatments match sample (delete old treatments for idempotency)
            # We'll keep it simple: remove existing treatments and recreate as per sample
            if sample.get("treatments"):
                rec.treatments.all().delete()
                for t in sample["treatments"]:
                    Treatment.objects.create(
                        recommendation=rec,
                        type=t.get("type", "chemical"),
                        name=t.get("name", ""),
                        active_ingredient=t.get("active_ingredient", ""),
                        dose_text=t.get("dose_text", ""),
                        application_method=t.get("application_method", ""),
                        pre_harvest_interval=t.get("pre_harvest_interval", ""),
                        ppe=t.get("ppe", ""),
                        notes=t.get("notes", ""),
                        source=t.get("source", ""),
                    )
                self.stdout.write(self.style.SUCCESS(f"  -> {len(sample['treatments'])} treatment(s) created for '{code}'"))

        # optional: create sample dealers if none exist (keeps feature handy for testing)
        if Dealer.objects.count() == 0:
            Dealer.objects.create(
                name="Kutsaga Agrovet",
                type="agrovet",
                city="Harare",
                province="Harare",
                country="Zimbabwe",
                latitude=-17.800,
                longitude=31.000,
                contact_name="John Doe",
                contact_phone="+263772000000",
                contact_email="kutsaga@example.com",
                inventory_tags="fungicide,azoxystrobin"
            )
            Dealer.objects.create(
                name="Borrowdale Agrodealer",
                type="agrodealer",
                city="Harare",
                province="Harare",
                country="Zimbabwe",
                latitude=-17.820,
                longitude=31.040,
                contact_name="Jane Doe",
                contact_phone="+263772111111",
                contact_email="dealer@example.com",
                inventory_tags="sprayer,chemicals"
            )
            self.stdout.write(self.style.SUCCESS("Created 2 sample dealers."))

        self.stdout.write(self.style.SUCCESS(f"Seed complete. created: {created_count}, updated: {updated_count}"))
