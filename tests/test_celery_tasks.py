import pytest
from django.conf import settings

from app.models import BackgroundTask, ClickEvent, DeviceType, ShortURL, TaskStatus
from app.tasks import ping
from app.tasks.analytics import get_device_information, track_click_task
from tests.mixins.mixins import ShortURLMixin


# ---------------------------------------------------------------------------
# Ping task tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ping_task_execution():
    res = ping.apply()
    assert res.result == "pong"

    task_record = BackgroundTask.objects.filter(task_id=res.id).first()
    assert task_record is not None
    assert task_record.status == TaskStatus.SUCCESS
    assert task_record.finished_at is not None

    events = list(task_record.events.values_list("message", flat=True))
    assert any("Sending Pong" in msg for msg in events)


def test_celery_settings():
    assert hasattr(settings, "CELERY_BROKER_URL")
    assert hasattr(settings, "CELERY_RESULT_BACKEND")
    assert settings.CELERY_TASK_TRACK_STARTED is True
    assert settings.CELERY_ACCEPT_CONTENT == ["json"]


# ---------------------------------------------------------------------------
# get_device_information tests
# ---------------------------------------------------------------------------

DESKTOP_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MOBILE_SAFARI_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

TABLET_IPAD_UA = (
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

BOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

FIREFOX_LINUX_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
)

EDGE_WINDOWS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
)


class TestGetDeviceInformation:
    """Tests for the get_device_information helper function."""

    def test_desktop_chrome(self):
        browser, os_name, device_type = get_device_information(DESKTOP_CHROME_UA)
        assert browser == "Chrome"
        assert os_name == "Windows"
        assert device_type == DeviceType.DESKTOP

    def test_mobile_safari(self):
        browser, os_name, device_type = get_device_information(MOBILE_SAFARI_UA)
        assert browser == "Mobile Safari"
        assert os_name == "iOS"
        assert device_type == DeviceType.MOBILE

    def test_tablet_ipad(self):
        browser, os_name, device_type = get_device_information(TABLET_IPAD_UA)
        assert browser == "Mobile Safari"
        assert os_name == "iOS"
        assert device_type == DeviceType.TABLET

    def test_bot_googlebot(self):
        browser, os_name, device_type = get_device_information(BOT_UA)
        assert device_type == DeviceType.BOT

    def test_firefox_linux(self):
        browser, os_name, device_type = get_device_information(FIREFOX_LINUX_UA)
        assert browser == "Firefox"
        assert os_name == "Linux"
        assert device_type == DeviceType.DESKTOP

    def test_edge_windows(self):
        browser, os_name, device_type = get_device_information(EDGE_WINDOWS_UA)
        assert browser == "Edge"
        assert os_name == "Windows"
        assert device_type == DeviceType.DESKTOP

    def test_returns_tuple_of_three(self):
        result = get_device_information(DESKTOP_CHROME_UA)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_empty_user_agent(self):
        browser, os_name, device_type = get_device_information("")
        assert browser is not None
        assert os_name is not None
        assert device_type in [
            DeviceType.UNKNOWN,
            DeviceType.BOT,
            DeviceType.DESKTOP,
        ]

    def test_unknown_user_agent(self):
        browser, os_name, device_type = get_device_information("SomeRandomString/1.0")
        assert isinstance(browser, str)
        assert isinstance(os_name, str)
        assert device_type in [v for v, _ in DeviceType.choices]


# ---------------------------------------------------------------------------
# track_click_task tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTrackClickTask(ShortURLMixin):
    """Tests for the track_click_task Celery task."""

    def _run_task(self, **kwargs):
        return track_click_task.apply(kwargs=kwargs)

    def test_creates_click_event(self):
        su = self.create_short_url(short_code="abc")
        res = self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        assert res.successful()
        assert ClickEvent.objects.filter(short_url=su).exists()

    def test_increments_click_count(self):
        su = self.create_short_url(short_code="cnt", click_count=0)
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        su.refresh_from_db()
        assert su.click_count == 1

    def test_multiple_clicks_increment_count(self):
        su = self.create_short_url(short_code="mul", click_count=0)
        for _ in range(3):
            self._run_task(
                short_url_id=su.pk,
                user_agent=DESKTOP_CHROME_UA,
                referer="",
            )
        su.refresh_from_db()
        assert su.click_count == 3

    def test_sets_last_clicked_at(self):
        su = self.create_short_url(short_code="lca", last_clicked_at=None)
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        su.refresh_from_db()
        assert su.last_clicked_at is not None

    def test_stores_browser_info(self):
        su = self.create_short_url(short_code="brw")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.browser == "Chrome"

    def test_stores_device_type_mobile(self):
        su = self.create_short_url(short_code="dvm")
        self._run_task(
            short_url_id=su.pk,
            user_agent=MOBILE_SAFARI_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.device_type == DeviceType.MOBILE

    def test_stores_device_type_desktop(self):
        su = self.create_short_url(short_code="dvd")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.device_type == DeviceType.DESKTOP

    def test_stores_device_type_tablet(self):
        su = self.create_short_url(short_code="dvt")
        self._run_task(
            short_url_id=su.pk,
            user_agent=TABLET_IPAD_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.device_type == DeviceType.TABLET

    def test_stores_country(self):
        su = self.create_short_url(short_code="cny")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
            country="India",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.country == "India"

    def test_country_defaults_to_empty(self):
        su = self.create_short_url(short_code="dft")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.country == ""

    def test_stores_referer(self):
        su = self.create_short_url(short_code="ref")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="https://google.com",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.referer == "https://google.com"

    def test_stores_user_agent(self):
        su = self.create_short_url(short_code="uag")
        self._run_task(
            short_url_id=su.pk,
            user_agent="MyCustomBot/1.0",
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.user_agent == "MyCustomBot/1.0"

    def test_empty_user_agent(self):
        su = self.create_short_url(short_code="eua")
        res = self._run_task(
            short_url_id=su.pk,
            user_agent="",
            referer="",
        )
        assert res.successful()
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.user_agent == ""
        assert event.device_type is not None

    def test_click_event_count_matches(self):
        su = self.create_short_url(short_code="ecs")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        assert ClickEvent.objects.filter(short_url=su).count() == 2

    def test_nonexistent_short_url_raises(self):
        result = track_click_task.apply(
            kwargs={
                "short_url_id": 99999,
                "user_agent": DESKTOP_CHROME_UA,
                "referer": "",
            }
        )
        assert result.failed()
        assert isinstance(result.result, ShortURL.DoesNotExist)

    def test_stores_operating_system(self):
        su = self.create_short_url(short_code="oso")
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.operating_system == "Windows"

    def test_stores_bot_device_type(self):
        su = self.create_short_url(short_code="bot")
        self._run_task(
            short_url_id=su.pk,
            user_agent=BOT_UA,
            referer="",
        )
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.device_type == DeviceType.BOT

    def test_sets_clicked_at_timestamp(self):
        su = self.create_short_url(short_code="cat")
        res = self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="",
        )
        assert res.successful()
        event = ClickEvent.objects.filter(short_url=su).first()
        assert event.clicked_at is not None

    def test_transaction_atomicity(self):
        su = self.create_short_url(short_code="txn", click_count=0)
        self._run_task(
            short_url_id=su.pk,
            user_agent=DESKTOP_CHROME_UA,
            referer="https://example.com",
            country="US",
        )
        su.refresh_from_db()
        event = ClickEvent.objects.filter(short_url=su).first()
        assert su.click_count == 1
        assert event is not None
        assert event.browser == "Chrome"
        assert event.country == "US"
        assert event.referer == "https://example.com"
        assert event.operating_system == "Windows"
        assert event.device_type == DeviceType.DESKTOP
