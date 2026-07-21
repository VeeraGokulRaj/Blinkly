import pytest
from unittest.mock import patch
from django.http import Http404
from django.test import RequestFactory

from app.views.redirect import redirect_view
from tests.mixins.mixins import ShortURLMixin


@pytest.mark.django_db
class TestRedirectView(ShortURLMixin):
    def test_redirects_to_original_url(self):
        self.create_short_url(
            original_url="https://example.com/target",
            short_code="red1",
        )
        request = RequestFactory().get("/red1/")
        response = redirect_view(request, "red1")
        assert response.status_code == 302
        assert response.url == "https://example.com/target"

    def test_returns_404_for_nonexistent_short_code(self):
        request = RequestFactory().get("/doesnotexist/")
        with pytest.raises(Http404):
            redirect_view(request, "doesnotexist")

    @patch("app.views.redirect.redirect_short_url")
    def test_calls_redirect_short_url(self, mock_redirect):
        mock_redirect.return_value = "https://example.com"
        request = RequestFactory().get("/test/")
        redirect_view(request, "test")
        mock_redirect.assert_called_once()

    def test_redirect_for_different_urls(self):
        self.create_short_url(
            original_url="https://first.com",
            short_code="aaa",
        )
        self.create_short_url(
            original_url="https://second.com",
            short_code="bbb",
        )
        request = RequestFactory().get("/aaa/")
        response = redirect_view(request, "aaa")
        assert response.url == "https://first.com"

        request2 = RequestFactory().get("/bbb/")
        response2 = redirect_view(request2, "bbb")
        assert response2.url == "https://second.com"

    def test_redirect_preserves_full_url(self):
        self.create_short_url(
            original_url="https://example.com/path?q=search&page=1#section",
            short_code="furl",
        )
        request = RequestFactory().get("/furl/")
        response = redirect_view(request, "furl")
        assert response.url == "https://example.com/path?q=search&page=1#section"
