import pytest

from app.tasks.analytics import get_device_information, track_click_task
from app.models import ClickEvent, DeviceType
from tests.mixins.mixins import ShortURLMixin


@pytest.mark.django_db
class TestGetDeviceInformation:
    def test_desktop_chrome(self):
        ua_string = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert browser == "Chrome"
        assert os_name == "Windows"
        assert device_type == DeviceType.DESKTOP

    def test_mobile_safari(self):
        ua_string = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert device_type == DeviceType.MOBILE

    def test_tablet(self):
        ua_string = (
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert device_type == DeviceType.TABLET

    def test_bot(self):
        ua_string = (
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert device_type == DeviceType.BOT

    def test_empty_ua(self):
        browser, os_name, device_type = get_device_information("")
        assert browser is not None
        assert os_name is not None
        assert device_type in [
            DeviceType.UNKNOWN,
            DeviceType.BOT,
            DeviceType.DESKTOP,
        ]

    def test_returns_tuple_of_three(self):
        result = get_device_information("Mozilla/5.0 (compatible; MSIE 10.0)")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_firefox_linux(self):
        ua_string = (
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert browser == "Firefox"
        assert os_name == "Linux"
        assert device_type == DeviceType.DESKTOP

    def test_edge_windows(self):
        ua_string = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        browser, os_name, device_type = get_device_information(ua_string)
        assert browser == "Edge"
        assert os_name == "Windows"
        assert device_type == DeviceType.DESKTOP


@pytest.mark.django_db
class TestTrackClickTask(ShortURLMixin):
    @staticmethod
    def _run_task(short_url_id, user_agent="", referer="", country=""):
        track_click_task.apply(
            kwargs={
                "short_url_id": short_url_id,
                "user_agent": user_agent,
                "referer": referer,
                "country": country,
            }
        )

    def test_creates_click_event(self):
        su = self.create_short_url(short_code="abc")
        self._run_task(
            su.pk,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        )
        assert ClickEvent.objects.filter(short_url=su).exists()

    def test_increments_click_count(self):
        su = self.create_short_url(short_code="cnt", click_count=0)
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        su.refresh_from_db()
        assert su.click_count == 1

    def test_multiple_clicks_increment_count(self):
        su = self.create_short_url(short_code="mul", click_count=0)
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        su.refresh_from_db()
        assert su.click_count == 3

    def test_sets_last_clicked_at(self):
        su = self.create_short_url(short_code="lca", last_clicked_at=None)
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        su.refresh_from_db()
        assert su.last_clicked_at is not None

    def test_stores_browser_info(self):
        su = self.create_short_url(short_code="brw")
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        self._run_task(su.pk, user_agent=ua)
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.browser == "Chrome"

    def test_stores_device_type(self):
        su = self.create_short_url(short_code="dvc")
        ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
        )
        self._run_task(su.pk, user_agent=ua)
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.device_type == DeviceType.MOBILE

    def test_stores_country(self):
        su = self.create_short_url(short_code="cny")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0", country="India")
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.country == "India"

    def test_stores_referer(self):
        su = self.create_short_url(short_code="ref")
        self._run_task(
            su.pk,
            user_agent="Chrome/120.0.0.0",
            referer="https://google.com",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.referer == "https://google.com"

    def test_stores_user_agent(self):
        su = self.create_short_url(short_code="uag")
        ua = "MyCustomBot/1.0"
        self._run_task(su.pk, user_agent=ua)
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.user_agent == ua

    def test_empty_user_agent(self):
        su = self.create_short_url(short_code="eua")
        self._run_task(su.pk, user_agent="")
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.user_agent == ""
        assert event.device_type is not None

    def test_country_defaults_to_empty(self):
        su = self.create_short_url(short_code="dft")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.country == ""

    def test_click_event_count_matches(self):
        su = self.create_short_url(short_code="ecs")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        self._run_task(su.pk, user_agent="Chrome/120.0.0.0")
        assert ClickEvent.objects.filter(short_url=su).count() == 2
