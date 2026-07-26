import pytest
from unittest.mock import patch

from app.domain.short_url import (
    BASE62_ALPHABET,
    BASE,
    MIN_SHORT_CODE_LENGTH,
    PUBLIC_ID_OFFSET,
    create_short_url,
    encode,
    extract_domain,
    generate_short_code,
)
from app.models import ShortURL


@pytest.mark.django_db
class TestEncode:
    def test_encode_zero_returns_first_character(self):
        assert encode(0) == BASE62_ALPHABET[0]

    def test_encode_one_returns_second_character(self):
        assert encode(1) == BASE62_ALPHABET[1]

    def test_encode_base_value(self):
        assert encode(BASE) == BASE62_ALPHABET[1] + BASE62_ALPHABET[0]

    def test_encode_returns_string(self):
        assert isinstance(encode(100), str)

    def test_encode_output_uses_only_base62_characters(self):
        result = encode(123456789)
        for char in result:
            assert char in BASE62_ALPHABET

    def test_encode_deterministic(self):
        assert encode(42) == encode(42)

    def test_encode_large_number(self):
        result = encode(10**12)
        assert len(result) > 0
        for char in result:
            assert char in BASE62_ALPHABET

    @pytest.mark.parametrize(
        "number, expected",
        [
            (0, BASE62_ALPHABET[0]),
            (1, BASE62_ALPHABET[1]),
        ],
    )
    def test_encode_parametrized(self, number, expected):
        assert encode(number) == expected


@pytest.mark.django_db
class TestGenerateShortCode:
    def test_returns_string(self):
        assert isinstance(generate_short_code(1), str)

    def test_minimum_length(self):
        code = generate_short_code(1)
        assert len(code) >= MIN_SHORT_CODE_LENGTH

    def test_deterministic_for_same_pk(self):
        assert generate_short_code(5) == generate_short_code(5)

    def test_different_pks_produce_different_codes(self):
        code_a = generate_short_code(1)
        code_b = generate_short_code(2)
        assert code_a != code_b

    def test_uses_public_id_offset(self):
        with patch("app.domain.short_url.encode") as mock_encode:
            mock_encode.return_value = "abc"
            generate_short_code(10)
            mock_encode.assert_called_once_with(10 + PUBLIC_ID_OFFSET)

    def test_output_uses_only_base62_characters(self):
        result = generate_short_code(999)
        for char in result:
            assert char in BASE62_ALPHABET


@pytest.mark.django_db
class TestExtractDomain:
    def test_simple_https_url(self):
        assert extract_domain("https://example.com/path") == "example.com"

    def test_simple_http_url(self):
        assert extract_domain("http://example.com") == "example.com"

    def test_url_with_port(self):
        assert extract_domain("https://example.com:8080/x") == "example.com:8080"

    def test_url_with_subdomain(self):
        assert extract_domain("https://blog.example.com/post") == "blog.example.com"

    def test_url_with_path_and_query(self):
        url = "https://example.com/path?q=search&page=1"
        assert extract_domain(url) == "example.com"

    def test_url_with_auth(self):
        url = "https://user:pass@example.com/"
        assert extract_domain(url) == "user:pass@example.com"

    def test_empty_string(self):
        assert extract_domain("") == ""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://google.com", "google.com"),
            ("http://localhost:3000", "localhost:3000"),
            ("https://sub.domain.co.uk/path", "sub.domain.co.uk"),
        ],
    )
    def test_parametrized(self, url, expected):
        assert extract_domain(url) == expected


@pytest.mark.django_db
class TestCreateShortUrlNestedUrl:
    def test_nested_url_returns_existing_short_url(self):
        existing = create_short_url("https://example.com/real-target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}"
        result = create_short_url(nested_url)
        assert result.pk == existing.pk
        assert result.original_url == "https://example.com/real-target"

    def test_nested_url_does_not_create_self_referencing_url(self):
        existing = create_short_url("https://example.com/target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}"
        result = create_short_url(nested_url)
        assert result.original_url != nested_url

    def test_nested_url_with_nonexistent_short_code_creates_new(self):
        nested_url = "http://127.0.0.1:8001/nocode"
        result = create_short_url(nested_url)
        assert result.pk is not None
        assert result.original_url == nested_url

    def test_nested_url_with_path_segments_does_not_resolve(self):
        existing = create_short_url("https://example.com/seg-target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}/extra/path"
        result = create_short_url(nested_url)
        assert result.pk != existing.pk
        assert result.original_url == nested_url

    def test_non_nested_url_with_same_path_not_treated_as_nested(self):
        existing = create_short_url("https://example.com/abc")
        normal_url = f"https://other-site.com/{existing.short_code}"
        result = create_short_url(normal_url)
        assert result.pk != existing.pk
        assert result.original_url == normal_url

    def test_nested_url_with_query_params_not_resolved(self):
        existing = create_short_url("https://example.com/qp-target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}?ref=home"
        result = create_short_url(nested_url)
        assert result.pk != existing.pk
        assert result.original_url == nested_url

    def test_nested_url_with_fragment_not_resolved(self):
        existing = create_short_url("https://example.com/frag-target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}#section"
        result = create_short_url(nested_url)
        assert result.pk != existing.pk
        assert result.original_url == nested_url

    def test_nested_url_with_query_and_fragment_not_resolved(self):
        existing = create_short_url("https://example.com/both-target")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}?ref=home#section"
        result = create_short_url(nested_url)
        assert result.pk != existing.pk
        assert result.original_url == nested_url

    def test_nested_url_with_empty_query_resolves(self):
        existing = create_short_url("https://example.com/empty-qp")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}?"
        result = create_short_url(nested_url)
        assert result.pk == existing.pk

    def test_nested_url_exact_match_resolves(self):
        existing = create_short_url("https://example.com/exact")
        nested_url = f"http://127.0.0.1:8001/{existing.short_code}"
        result = create_short_url(nested_url)
        assert result.pk == existing.pk
        assert result.original_url == "https://example.com/exact"


@pytest.mark.django_db
class TestCreateShortUrl:
    def test_creates_new_short_url(self):
        url = "https://example.com/new"
        short_url = create_short_url(url)
        assert short_url.pk is not None
        assert short_url.original_url == url
        assert short_url.target_domain == "example.com"
        assert len(short_url.short_code) >= MIN_SHORT_CODE_LENGTH

    def test_returns_same_on_duplicate(self):
        url = "https://example.com/dup"
        first = create_short_url(url)
        second = create_short_url(url)
        assert first.pk == second.pk
        assert ShortURL.objects.filter(original_url=url).count() == 1

    def test_short_code_is_unique(self):
        su1 = create_short_url("https://a.com/1")
        su2 = create_short_url("https://b.com/2")
        assert su1.short_code != su2.short_code

    def test_click_count_defaults_to_zero(self):
        short_url = create_short_url("https://example.com/clicks")
        assert short_url.click_count == 0

    def test_last_clicked_at_is_none_initially(self):
        short_url = create_short_url("https://example.com/noclick")
        assert short_url.last_clicked_at is None

    def test_creates_record_in_database(self):
        url = "https://example.com/db"
        create_short_url(url)
        assert ShortURL.objects.filter(original_url=url).exists()

    def test_target_domain_extracted(self):
        short_url = create_short_url("https://blog.example.com/article")
        assert short_url.target_domain == "blog.example.com"

    def test_short_code_stored_in_database(self):
        short_url = create_short_url("https://example.com/store")
        from_db = ShortURL.objects.get(pk=short_url.pk)
        assert from_db.short_code == short_url.short_code
