"""Tests détection DATE_NAISSANCE — exige mot-clé proximité."""

import pytest

from anonymizer import Anonymizer


@pytest.fixture
def anon():
    return Anonymizer()


def _has_tag(text: str, prefix: str = "[DATE_NAISSANCE_") -> bool:
    return prefix in text


class TestDateNaissancePositive:
    def test_ne_le(self, anon):
        out = anon.anonymize("Jean est né le 14/07/1985 à Paris.")
        assert _has_tag(out)
        assert "14/07/1985" not in out

    def test_nee_le_feminin(self, anon):
        out = anon.anonymize("Marie née le 03-12-1990.")
        assert _has_tag(out)
        assert "03-12-1990" not in out

    def test_nee_parenthese(self, anon):
        out = anon.anonymize("Sophie né(e) le 1.4.1978")
        assert _has_tag(out)

    def test_date_naissance_keyword(self, anon):
        out = anon.anonymize("Date de naissance : 22/05/1972")
        assert _has_tag(out)

    def test_naissance_colon(self, anon):
        out = anon.anonymize("Naissance: 1985-07-14")
        assert _has_tag(out)

    def test_iso_format(self, anon):
        out = anon.anonymize("né le 1985-07-14")
        assert _has_tag(out)

    def test_dob_abbrev(self, anon):
        out = anon.anonymize("DOB: 15/03/1980")
        assert _has_tag(out)

    def test_born_on(self, anon):
        out = anon.anonymize("born on 1980-03-15")
        assert _has_tag(out)


class TestDateNaissanceNegative:
    """Dates sans mot-clé proximité ne doivent PAS être anonymisées."""

    def test_date_facture(self, anon):
        out = anon.anonymize("Facture émise le 14/07/2024.")
        assert not _has_tag(out)
        assert "14/07/2024" in out

    def test_date_version(self, anon):
        out = anon.anonymize("Version 1.2.2023 publiée hier.")
        assert not _has_tag(out)

    def test_date_intervention(self, anon):
        out = anon.anonymize("Intervention prévue le 05/06/2025.")
        assert not _has_tag(out)


class TestDateNaissanceMapping:
    def test_stable_mapping(self, anon):
        anon.anonymize("né le 14/07/1985 et né le 14/07/1985")
        # Même date → même tag
        tags = [t for t in anon.mapping.values() if t.startswith("[DATE_NAISSANCE_")]
        assert len(tags) == 1

    def test_deanonymize_restores(self, anon):
        original = "Patient né le 22/08/1965 admis."
        anon_text = anon.anonymize(original)
        restored = anon.deanonymize(anon_text)
        assert restored == original

    def test_keyword_preserved(self, anon):
        out = anon.anonymize("né le 14/07/1985")
        assert "né le" in out
        assert "[DATE_NAISSANCE_1]" in out
