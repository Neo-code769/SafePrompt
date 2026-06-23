from anonymizer import Anonymizer


def _anon(text):
    a = Anonymizer()
    a.nlp = None  # désactive spaCy pour tests rapides
    return a, a.anonymize(text)


def test_email_replaced():
    a, r = _anon("Contact : jean.dupont@acme.fr")
    assert "@acme.fr" not in r
    assert "[EMAIL_1]" in r


def test_ipv4_replaced():
    a, r = _anon("Le serveur 192.168.1.42 répond.")
    assert "192.168.1.42" not in r
    assert "[IPv4_1]" in r


def test_mac_replaced():
    a, r = _anon("MAC: 00:1A:2B:3C:4D:5E")
    assert "[MAC_1]" in r


def test_invalid_pan_kept():
    """Faux PAN (échec Luhn) → laissé intact."""
    text = "Référence : 1234 5678 9012 3456"
    a, r = _anon(text)
    assert "1234 5678 9012 3456" in r
    assert "[CB_" not in r


def test_valid_pan_replaced():
    text = "Carte : 4532 0151 1283 0366"
    a, r = _anon(text)
    assert "[CB_1]" in r


def test_invalid_iban_kept():
    a, r = _anon("Ref FR1420041010050500013M02600 invalide")
    assert "[IBAN_" not in r


def test_valid_iban_replaced():
    a, r = _anon("IBAN : DE89370400440532013000")
    assert "[IBAN_1]" in r


def test_deanonymize_roundtrip():
    a = Anonymizer()
    a.nlp = None
    src = "Envoyer à test@ex.com depuis 10.0.0.1"
    anon = a.anonymize(src)
    assert a.deanonymize(anon) == src


def test_mapping_stable():
    a = Anonymizer()
    a.nlp = None
    a.anonymize("mail: a@b.fr")
    r2 = a.anonymize("mail: a@b.fr again")
    assert r2.count("[EMAIL_1]") == 1
