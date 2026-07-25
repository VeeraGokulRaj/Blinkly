import pytest
from unittest.mock import patch
from django.http import Http404
from django.test import RequestFactory
from django.core.cache import cache

from app.domain.redirect import redirect_short_url, set_short_url_cache
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


@pytest.mark.django_db
class TestRedirectShortUrlCache(ShortURLMixin):
    def setup_method(self):
        cache.clear()

    @patch("app.domain.redirect.track_click_task")
    def test_cache_is_set_after_db_fetch(self, mock_task):
        self.create_short_url(
            original_url="https://example.com/cached",
            short_code="cache1",
        )
        request = RequestFactory().get("/")
        redirect_short_url(request, "cache1")

        cached = cache.get("short_url:cache1")
        assert cached is not None
        assert cached["original_url"] == "https://example.com/cached"
        assert isinstance(cached["id"], int)

    @patch("app.domain.redirect.track_click_task")
    def test_cache_hit_skips_db(self, mock_task):
        self.create_short_url(
            original_url="https://example.com/hit",
            short_code="hit1",
        )
        request = RequestFactory().get("/")

        redirect_short_url(request, "hit1")
        redirect_short_url(request, "hit1")

        assert mock_task.delay.call_count == 2

    @patch("app.domain.redirect.track_click_task")
    def test_cache_returns_correct_url(self, mock_task):
        self.create_short_url(
            original_url="https://example.com/right",
            short_code="right1",
        )
        request = RequestFactory().get("/")

        redirect_short_url(request, "right1")
        cached = cache.get("short_url:right1")
        assert cached["original_url"] == "https://example.com/right"

    @patch("app.domain.redirect.track_click_task")
    def test_cache_uses_correct_key_format(self, mock_task):
        self.create_short_url(short_code="key1")
        request = RequestFactory().get("/")
        redirect_short_url(request, "key1")

        assert cache.get("short_url:key1") is not None

    @patch("app.domain.redirect.track_click_task")
    def test_different_short_codes_have_separate_cache(self, mock_task):
        self.create_short_url(
            original_url="https://a.com",
            short_code="sep_a",
        )
        self.create_short_url(
            original_url="https://b.com",
            short_code="sep_b",
        )
        request = RequestFactory().get("/")

        redirect_short_url(request, "sep_a")
        redirect_short_url(request, "sep_b")

        assert cache.get("short_url:sep_a")["original_url"] == "https://a.com"
        assert cache.get("short_url:sep_b")["original_url"] == "https://b.com"

    def test_404_not_cached(self):
        request = RequestFactory().get("/")
        with pytest.raises(Http404):
            redirect_short_url(request, "nocache")

        assert cache.get("short_url:nocache") is None

    @patch("app.domain.redirect.track_click_task")
    def test_set_short_url_cache_returns_correct_dict(self, mock_task):
        su = self.create_short_url(
            original_url="https://example.com/dict",
            short_code="dict1",
        )
        result = set_short_url_cache("dict1")
        assert result == {"id": su.pk, "original_url": "https://example.com/dict"}

    @patch("app.domain.redirect.track_click_task")
    def test_set_short_url_cache_raises_for_nonexistent(self, mock_task):
        with pytest.raises(Http404):
            set_short_url_cache("nonexistent")

    @patch("app.domain.redirect.track_click_task")
    def test_cache_has_id_for_track_click(self, mock_task):
        su = self.create_short_url(
            original_url="https://example.com/id",
            short_code="id1",
        )
        request = RequestFactory().get("/")
        redirect_short_url(request, "id1")

        cached = cache.get("short_url:id1")
        assert cached["id"] == su.pk
        mock_task.delay.assert_called_once_with(
            short_url_id=su.pk,
            user_agent="",
            referer="",
            country="",
        )
