from urllib.parse import urlparse
from django.core.exceptions import ValidationError

from django.db import transaction

from app.models import ShortURL
from config.settings.base import SITE_URL

BASE62_ALPHABET = "k3G8am0LzQvBxW5C2rNh7AfyYtZsE1pdjc9eXUMi4VJqo6uKHIblFOgRwPnTS"
BASE = len(BASE62_ALPHABET)
MIN_SHORT_CODE_LENGTH = 3
PUBLIC_ID_OFFSET = (62 ** (MIN_SHORT_CODE_LENGTH - 1)) - 1


def create_short_url(original_url: str) -> ShortURL:
    """
    Create a shortened URL or return the existing one.
    """
    with transaction.atomic():
        existing = get_existing_short_url(original_url)

        if existing:
            return existing

        short_url = ShortURL.objects.create(
            original_url=original_url,
            target_domain=extract_domain(original_url),
        )

        short_url.short_code = generate_short_code(short_url.pk)
        short_url.save(update_fields=["short_code"])

        return short_url


def get_existing_short_url(original_url: str) -> ShortURL | None:
    """
    Return an existing short URL for the given URL, if one exists.
    """

    parsed = urlparse(original_url)
    site = urlparse(SITE_URL)

    if parsed.netloc == site.netloc:
        if parsed.query or parsed.fragment:
            raise ValidationError(
                "Blinkly URLs with query parameters or fragments cannot be shortened."
            )

        return ShortURL.objects.filter(
            short_code=parsed.path.strip("/"),
        ).first()

    return ShortURL.objects.filter(
        original_url=original_url,
    ).first()


def extract_domain(url: str) -> str:
    """
    Extract the domain from the URL.
    """

    return urlparse(url).netloc


def generate_short_code(pk: int) -> str:
    """
    Generate a deterministic short code.
    """

    return encode(pk + PUBLIC_ID_OFFSET)


def encode(number: int) -> str:
    """
    Encode an integer using the configured Base62 alphabet.
    """
    if number == 0:
        return BASE62_ALPHABET[0]

    encoded = []

    while number:
        number, remainder = divmod(number, BASE)
        encoded.append(BASE62_ALPHABET[remainder])

    return "".join(reversed(encoded))
