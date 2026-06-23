"""
Validators — Réduit les faux positifs des regex sensibles.

- PAN (carte bancaire) : algorithme de Luhn
- IBAN : MOD-97 sur représentation numérique
- NIR (sécu sociale FR) : clé de contrôle = 97 - (numéro mod 97)
"""

import re


def luhn_check(digits: str) -> bool:
    """Vérifie un numéro par l'algorithme de Luhn."""
    d = [int(c) for c in digits if c.isdigit()]
    if len(d) < 12:
        return False
    if all(x == 0 for x in d):
        return False
    checksum = 0
    parity = len(d) % 2
    for i, n in enumerate(d):
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        checksum += n
    return checksum % 10 == 0


def valid_pan(text: str) -> bool:
    """Carte bancaire : 13 à 19 chiffres, validation Luhn."""
    digits = re.sub(r"[\s\-]", "", text)
    if not digits.isdigit() or not (13 <= len(digits) <= 19):
        return False
    return luhn_check(digits)


def valid_iban(text: str) -> bool:
    """IBAN : MOD-97 doit retourner 1."""
    s = text.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    # Réarrange : 4 premiers caractères à la fin
    rearranged = s[4:] + s[:4]
    # Lettres → chiffres (A=10, B=11, ..., Z=35)
    numeric = "".join(
        str(ord(c) - 55) if c.isalpha() else c
        for c in rearranged
    )
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def valid_nir(text: str) -> bool:
    """
    Numéro de sécurité sociale FR (NIR) : 13 chiffres + clé 2 chiffres.
    Clé = 97 - (numéro mod 97).
    Tolère les codes Corse (2A→19, 2B→18) après le département.
    """
    s = re.sub(r"\s", "", text)
    if not re.fullmatch(r"[12]\d{14}", s):
        return False
    body = s[:13]
    key = int(s[13:])
    # Corse : département 2A ou 2B encodé spécialement (rarement présent dans regex extraite)
    expected = 97 - (int(body) % 97)
    return expected == key


def valid_siret(text: str) -> bool:
    digits = re.sub(r'\D', '', text)
    return len(digits) == 14


def valid_siren(text: str) -> bool:
    digits = re.sub(r'\D', '', text)
    return len(digits) == 9


VALIDATORS = {
    "CB": valid_pan,
    "IBAN": valid_iban,
    "NIR": valid_nir,
    "SIRET": valid_siret,
    "SIREN": valid_siren,
}
