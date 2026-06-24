from validators import luhn_check, valid_iban, valid_nir, valid_pan, valid_siren, valid_siret


class TestLuhn:
    def test_known_valid(self):
        assert luhn_check("4532015112830366")  # Visa de test
        assert luhn_check("5500000000000004")  # MasterCard de test

    def test_known_invalid(self):
        assert not luhn_check("1234567812345678")
        assert not luhn_check("0000000000000000")


class TestPAN:
    def test_valid_with_spaces(self):
        assert valid_pan("4532 0151 1283 0366")

    def test_valid_with_dashes(self):
        assert valid_pan("4532-0151-1283-0366")

    def test_invalid_random(self):
        assert not valid_pan("1234 5678 9012 3456")

    def test_too_short(self):
        assert not valid_pan("4532 0151")


class TestIBAN:
    def test_valid_fr(self):
        # IBAN FR de test (clé recalculée)
        assert valid_iban("FR1420041010050500013M02606")

    def test_valid_de(self):
        assert valid_iban("DE89370400440532013000")

    def test_invalid_checksum(self):
        assert not valid_iban("FR1420041010050500013M02600")

    def test_invalid_format(self):
        assert not valid_iban("XX99")


class TestNIR:
    def test_valid(self):
        # NIR fictif avec clé correcte
        body = "180127512345698"
        key = 97 - (int(body[:13]) % 97)
        nir = body[:13] + f"{key:02d}"
        assert valid_nir(nir)

    def test_invalid_key(self):
        assert not valid_nir("180127512345699999")

    def test_wrong_prefix(self):
        assert not valid_nir("380127512345698")


class TestSIRET:
    def test_valid(self):
        assert valid_siret("38012986600006")

    def test_valid_formatted(self):
        assert valid_siret("380 129 866 00006")

    def test_invalid_luhn(self):
        assert not valid_siret("38012986600007")

    def test_wrong_length(self):
        assert not valid_siret("1234567890")


class TestSIREN:
    def test_valid(self):
        # SIREN Orange SA
        assert valid_siren("380129866")

    def test_invalid_luhn(self):
        assert not valid_siren("380129867")

    def test_wrong_length(self):
        assert not valid_siren("12345")
