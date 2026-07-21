from app.models import ClickEvent, DeviceType, ShortURL


class ShortURLMixin:
    @staticmethod
    def create_short_url(
        original_url=None,
        target_domain="example.com",
        short_code=None,
        click_count=0,
        **kwargs,
    ):
        if original_url is None:
            original_url = "https://example.com/test"
        if short_code is None:
            short_code = "test1"
        return ShortURL.objects.create(
            original_url=original_url,
            target_domain=target_domain,
            short_code=short_code,
            click_count=click_count,
            **kwargs,
        )


class ClickEventMixin:
    @staticmethod
    def create_click_event(
        short_url=None,
        browser="Chrome",
        operating_system="Windows",
        device_type=DeviceType.DESKTOP,
        country="",
        referer="",
        user_agent="",
        **kwargs,
    ):
        if short_url is None:
            short_url = ShortURLMixin.create_short_url()
        return ClickEvent.objects.create(
            short_url=short_url,
            browser=browser,
            operating_system=operating_system,
            device_type=device_type,
            country=country,
            referer=referer,
            user_agent=user_agent,
            **kwargs,
        )
