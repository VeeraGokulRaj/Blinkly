import pytest
from django.test import RequestFactory

from app.models import ShortURL
from app.views.short_url import create_short_url_view


@pytest.mark.django_db
class TestCreateShortUrlView:
    def test_get_returns_200(self):
        request = RequestFactory().get("/")
        response = create_short_url_view(request)
        assert response.status_code == 200

    def test_get_renders_base_template(self):
        request = RequestFactory().get("/")
        response = create_short_url_view(request)
        assert b"Blinkly" in response.content

    def test_get_has_empty_form(self):
        request = RequestFactory().get("/")
        response = create_short_url_view(request)
        assert b"Shorten" in response.content

    def test_post_valid_url_creates_short_url(self):
        request = RequestFactory().post("/", {"original_url": "https://example.com"})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert ShortURL.objects.filter(original_url="https://example.com").exists()

    def test_post_valid_url_shows_result(self):
        request = RequestFactory().post("/", {"original_url": "https://example.com"})
        response = create_short_url_view(request)
        assert b"Your shortened URL" in response.content
        assert b"https://example.com" in response.content

    def test_post_invalid_url_does_not_create(self):
        request = RequestFactory().post("/", {"original_url": "not-a-url"})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert ShortURL.objects.count() == 0

    def test_post_invalid_url_shows_form(self):
        request = RequestFactory().post("/", {"original_url": "not-a-url"})
        response = create_short_url_view(request)
        assert b"Shorten" in response.content

    def test_post_empty_url_does_not_create(self):
        request = RequestFactory().post("/", {"original_url": ""})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert ShortURL.objects.count() == 0

    def test_post_duplicate_url_returns_existing(self):
        request = RequestFactory().post("/", {"original_url": "https://dup.com"})
        create_short_url_view(request)
        request2 = RequestFactory().post("/", {"original_url": "https://dup.com"})
        create_short_url_view(request2)
        assert ShortURL.objects.filter(original_url="https://dup.com").count() == 1

    def test_get_returns_short_url_none(self):
        request = RequestFactory().get("/")
        response = create_short_url_view(request)
        assert b"Your shortened URL" not in response.content

    def test_post_url_at_max_length_creates_short_url(self):
        prefix = "https://example.com/"
        remaining = 2048 - len(prefix)
        url = prefix + ("a" * remaining)

        request = RequestFactory().post(
            "/",
            {"original_url": url},
        )

        response = create_short_url_view(request)

        assert response.status_code == 200
        assert ShortURL.objects.filter(original_url=url).exists()

    def test_post_blinkly_url_with_query_shows_validation_error(self):
        existing = ShortURL.objects.create(
            original_url="https://example.com/v",
            target_domain="example.com",
            short_code="vq",
        )
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}?ref=home"
        request = RequestFactory().post("/", {"original_url": nested_url})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert b"query parameters or fragments" in response.content

    def test_post_blinkly_url_with_fragment_shows_validation_error(self):
        existing = ShortURL.objects.create(
            original_url="https://example.com/f",
            target_domain="example.com",
            short_code="vf",
        )
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}#section"
        request = RequestFactory().post("/", {"original_url": nested_url})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert b"query parameters or fragments" in response.content

    def test_post_blinkly_url_clean_resolves_normally(self):
        existing = ShortURL.objects.create(
            original_url="https://example.com/clean",
            target_domain="example.com",
            short_code="vc",
        )
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}"
        request = RequestFactory().post("/", {"original_url": nested_url})
        response = create_short_url_view(request)
        assert response.status_code == 200
        assert b"Your shortened URL" in response.content
