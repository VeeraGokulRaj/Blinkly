import pytest
from unittest.mock import patch
from django.http import Http404
from django.test import RequestFactory

from app.domain.redirect import redirect_short_url
from tests.mixins.mixins import ShortURLMixin


@pytest.mark.django_db
class TestRedirectShortUrl(ShortURLMixin):
    def test_returns_original_url(self):
        self.create_short_url(
            original_url="https://example.com/target",
            short_code="abc123",
        )
        request = RequestFactory().get("/")
        result = redirect_short_url(request, "abc123")
        assert result == "https://example.com/target"

    def test_raises_404_for_nonexistent_code(self):
        request = RequestFactory().get("/")
        with pytest.raises(Http404):
            redirect_short_url(request, "nonexistent")

    @patch("app.domain.redirect.track_click_task")
    def test_calls_track_click_task(self, mock_task):
        self.create_short_url(short_code="xyz789")
        request = RequestFactory().get(
            "/",
            HTTP_USER_AGENT="Mozilla/5.0 TestAgent",
            HTTP_REFERER="https://google.com",
        )
        redirect_short_url(request, "xyz789")
        mock_task.delay.assert_called_once()

    @patch("app.domain.redirect.track_click_task")
    def test_returns_correct_url_for_different_short_code(self, mock_task):
        self.create_short_url(
            original_url="https://first.com",
            short_code="aaa",
        )
        self.create_short_url(
            original_url="https://second.com",
            short_code="bbb",
        )
        request = RequestFactory().get("/")
        result = redirect_short_url(request, "bbb")
        assert result == "https://second.com"

    def test_raises_404_for_empty_string(self):
        request = RequestFactory().get("/")
        with pytest.raises(Http404):
            redirect_short_url(request, "")

    def test_does_not_raise_for_valid_short_code(self):
        self.create_short_url(short_code="valid")
        request = RequestFactory().get("/")
        result = redirect_short_url(request, "valid")
        assert result is not None
