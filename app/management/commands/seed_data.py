import random
import string
from datetime import datetime
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from faker import Faker

from app.models import ClickEvent, DeviceType, ShortURL

fake = Faker()

BROWSERS = [
    "Chrome",
    "Firefox",
    "Edge",
    "Safari",
    "Opera",
]

OPERATING_SYSTEMS = [
    "Windows",
    "macOS",
    "Linux",
    "Android",
    "iOS",
]

COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Germany",
    "France",
    "Australia",
    "Singapore",
    "Japan",
    "Brazil",
]

REFERERS = [
    "https://google.com",
    "https://bing.com",
    "https://duckduckgo.com",
    "https://facebook.com",
    "https://linkedin.com",
    "https://reddit.com",
    "https://twitter.com",
    None,
]


class Command(BaseCommand):
    help = "Generate realistic seed data."

    def handle(self, *args, **options):
        start_date = datetime(2026, 1, 1, tzinfo=timezone.get_current_timezone())
        end_date = timezone.now()

        self.stdout.write("Creating test data...")

        with transaction.atomic():
            urls = []

            for _ in range(100):
                original_url = fake.url()

                short_url = ShortURL.objects.create(
                    original_url=original_url,
                    target_domain=urlparse(original_url).netloc,
                    short_code=self.random_short_code(),
                    click_count=150,
                )

                urls.append(short_url)

            events = []

            for short_url in urls:
                latest_click = start_date

                for _ in range(150):
                    clicked_at = fake.date_time_between(
                        start_date=start_date,
                        end_date=end_date,
                        tzinfo=timezone.get_current_timezone(),
                    )

                    if clicked_at > latest_click:
                        latest_click = clicked_at

                    events.append(
                        ClickEvent(
                            short_url=short_url,
                            clicked_at=clicked_at,
                            browser=random.choice(BROWSERS),
                            operating_system=random.choice(OPERATING_SYSTEMS),
                            device_type=random.choice(DeviceType.values),
                            country=random.choice(COUNTRIES),
                            referer=random.choice(REFERERS),
                            user_agent=fake.user_agent(),
                        )
                    )

                short_url.last_clicked_at = latest_click
                short_url.save(update_fields=["last_clicked_at"])

            ClickEvent.objects.bulk_create(events, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(urls)} ShortURLs and {len(events)} ClickEvents."
            )
        )

    @staticmethod
    def random_short_code(length=8):
        alphabet = string.ascii_letters + string.digits

        while True:
            code = "".join(random.choices(alphabet, k=length))
            if not ShortURL.objects.filter(short_code=code).exists():
                return code
