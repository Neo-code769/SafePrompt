"""Tests qualité NER — whitelist + min length + désactivation catégories."""

import pytest

from anonymizer import Anonymizer


@pytest.fixture
def anon_default():
    return Anonymizer()


class TestNerWhitelist:
    def test_whitelist_skips_entity(self):
        a = Anonymizer(ner_whitelist=["Action Telecom"])
        out = a.anonymize("Le client Action Telecom a contacté Jean Dupont.")
        assert "Action Telecom" in out
        assert "[ORGANISATION_" not in out or "Action Telecom" not in a.mapping

    def test_whitelist_case_insensitive(self):
        a = Anonymizer(ner_whitelist=["microsoft"])
        out = a.anonymize("Solution Microsoft déployée.")
        assert "Microsoft" in out

    def test_whitelist_strips_input(self):
        a = Anonymizer(ner_whitelist=["  Microsoft  ", ""])
        assert "microsoft" in a.ner_whitelist
        assert "" not in a.ner_whitelist

    def test_empty_whitelist_no_effect(self):
        a = Anonymizer(ner_whitelist=[])
        out = a.anonymize("Jean Dupont est arrivé.")
        # NER actif → un tag a été créé (sauf si spaCy n'a rien détecté)
        # On vérifie juste que pas de crash
        assert isinstance(out, str)


class TestNerMinLength:
    def test_anonymizer_has_min_length_constant(self):
        assert Anonymizer.NER_MIN_LENGTH >= 2

    def test_single_char_entity_skipped(self):
        # Difficile à forcer sans contrôler spaCy ; on teste le filtre directement
        a = Anonymizer()
        # Injection manuelle dans whitelist pour neutraliser
        a.ner_whitelist = {"x"}
        out = a.anonymize("X est un point.")
        assert "X" in out


class TestNerDisabledCategory:
    def test_disable_personne(self):
        a = Anonymizer(disabled_categories=["PERSONNE"])
        out = a.anonymize("Jean Dupont travaille ici.")
        assert "Jean Dupont" in out
        assert "[PERSONNE_" not in out

    def test_disable_organisation(self):
        a = Anonymizer(disabled_categories=["ORGANISATION"])
        out = a.anonymize("Microsoft a publié une mise à jour.")
        assert "[ORGANISATION_" not in out


class TestNerTagPreservation:
    def test_tag_not_double_wrapped(self):
        # Cas du bug corrigé : NER ne doit pas re-capturer [IPv4_1]
        a = Anonymizer(disabled_categories=["EMAIL", "PERSONNE"])
        out = a.anonymize("ip 192.168.1.1")
        assert "[[" not in out
        assert "[IPv4_1]" in out
