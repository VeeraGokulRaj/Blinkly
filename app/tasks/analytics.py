from django.db import transaction
from django.db.models import F
from django.utils import timezone

from user_agents import parse
from celery import shared_task


from app.models import ClickEvent, ShortURL, DeviceType


@shared_task
def track_click_task(
    *,
    short_url_id: int,
    user_agent: str,
    referer: str,
    country: str = "",
) -> None:
    """
    Record a click event and update aggregate statistics.
    """

    browser, operating_system, device_type = get_device_information(user_agent)

    with transaction.atomic():
        short_url = ShortURL.objects.get(pk=short_url_id)

        ClickEvent.objects.create(
            short_url=short_url,
            browser=browser,
            operating_system=operating_system,
            device_type=device_type,
            country=country,
            referer=referer,
            user_agent=user_agent,
        )

        ShortURL.objects.filter(pk=short_url_id).update(
            click_count=F("click_count") + 1,
            last_clicked_at=timezone.now(),
        )


def get_device_information(user_agent: str) -> tuple[str, str, str]:
    """
    Parse the user agent and return browser, operating system and device type.
    """

    ua = parse(user_agent)

    if ua.is_mobile:
        device_type = DeviceType.MOBILE
    elif ua.is_tablet:
        device_type = DeviceType.TABLET
    elif ua.is_pc:
        device_type = DeviceType.DESKTOP
    elif ua.is_bot:
        device_type = DeviceType.BOT
    else:
        device_type = DeviceType.UNKNOWN

    return (
        ua.browser.family,
        ua.os.family,
        device_type,
    )
