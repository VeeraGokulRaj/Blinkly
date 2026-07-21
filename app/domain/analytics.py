from django.db.models import F
from django.utils import timezone

from app.models import ClickEvent

from user_agents import parse

from app.models import DeviceType
from django.db import transaction


def track_click(request, short_url, country: str = "") -> None:
    """
    Record a click event and update the aggregate statistics.
    """
    with transaction.atomic():
        user_agent = request.headers.get("User-Agent", "")

        browser, operating_system, device_type = get_device_information(user_agent)

        ClickEvent.objects.create(
            short_url=short_url,
            browser=browser,
            operating_system=operating_system,
            device_type=device_type,
            country=country,
            referer=request.headers.get("Referer", ""),
            user_agent=user_agent,
        )

        type(short_url).objects.filter(
            pk=short_url.pk,
        ).update(
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
