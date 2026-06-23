from anonymizer import Anonymizer


def _anon(text):
    a = Anonymizer()
    a.nlp = None
    return a, a.anonymize(text)


def test_siret_with_keyword():
    a, r = _anon("SIRET: 732 829 320 00074")
    assert "[SIRET_1]" in r
    assert "732" not in r


def test_siret_contiguous_with_keyword():
    a, r = _anon("SIRET 73282932000074")
    assert "[SIRET_1]" in r


def test_siret_formatted_no_keyword():
    a, r = _anon("Référence 732 829 320 00074 dans le contrat.")
    assert "[SIRET_1]" in r


def test_siren_with_keyword():
    a, r = _anon("SIREN: 732 829 320")
    assert "[SIREN_1]" in r
    assert "732" not in r


def test_siren_no_keyword_not_replaced():
    """SIREN sans keyword ne doit pas être anonymisé (trop de faux positifs)."""
    a, r = _anon("Référence dossier 123456789.")
    assert "[SIREN_" not in r


def test_siret_before_code_postal():
    """Les 5 derniers chiffres du SIRET ne doivent pas devenir CODE_POSTAL."""
    a, r = _anon("SIRET: 732 829 320 00074")
    assert "[CODE_POSTAL_" not in r


def test_siret_deanonymize_roundtrip():
    a = Anonymizer()
    a.nlp = None
    src = "Client SIRET: 732 829 320 00074 - facture"
    anon = a.anonymize(src)
    assert a.deanonymize(anon) == src
