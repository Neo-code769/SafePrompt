#!/usr/bin/env python3
"""
Anonymiseur de données sensibles pour outils IA
================================================
Remplace automatiquement les informations sensibles par des marqueurs
avant de soumettre du texte à un outil IA.

Types détectés :
  - Noms / Prénoms (via NER spaCy)
  - Organisations (via NER spaCy)
  - Adresses postales / Villes (via NER spaCy + regex)
  - Adresses e-mail
  - Adresses IPv4 et IPv6
  - Adresses MAC
  - Numéros de téléphone (format FR)
  - Codes postaux français
  - Numéros IBAN
  - Ports réseau (notation explicite)
  - Noms de domaine internes / hostnames
  - Numéros de carte bancaire (PAN)
  - Numéros de sécurité sociale (NIR)
"""

import re
import json
import argparse
import sys
from pathlib import Path
from typing import Optional

from validators import VALIDATORS


# ─────────────────────────────────────────────
# Patterns regex
# ─────────────────────────────────────────────

PATTERNS = {
    "EMAIL": re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    ),
    "IPv4": re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    ),
    "IPv6": re.compile(
        r'\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b'
        r'|(?:[0-9a-fA-F]{1,4}:){1,6}:(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}'
        r'|::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}'
    ),
    "MAC": re.compile(
        r'\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b'
    ),
    "PORT_KEYWORD": re.compile(
        r'(?i)\b(ports?\s*[=:]\s*)(\d{1,5})\b'
    ),
    "TEL_FR": re.compile(
        r'\b(?:\+33|0033|0)\s?[1-9](?:[\s.\-]?\d{2}){4}\b'
    ),
    "CP_FR": re.compile(
        r'\b(?:0[1-9]|[1-8]\d|9[0-8])\d{3}\b'
    ),
    "IBAN": re.compile(
        r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]{0,16})\b'
    ),
    "PAN": re.compile(                          # Carte bancaire (PAN 16 chiffres)
        r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'
    ),
    "NIR": re.compile(                          # Numéro de sécu français
        r'\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b'
    ),
    "HOSTNAME": re.compile(                     # Hostnames internes (ex: srv-web01.lan)
        r'\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+(?:local|lan|intranet|internal|corp|home)\b',
        re.IGNORECASE
    ),
}


class Anonymizer:
    """
    Anonymise les données sensibles dans un texte.
    Un mapping bidirectionnel permet la dé-anonymisation.
    """

    def __init__(self, mapping_file: Optional[str] = None):
        self.mapping: dict[str, str] = {}          # original  -> [TAG_N]
        self.reverse_mapping: dict[str, str] = {}  # [TAG_N]   -> original
        self.counters: dict[str, int] = {}
        self.nlp = None

        if mapping_file and Path(mapping_file).exists():
            self._load_mapping(mapping_file)

        self._load_spacy()

    # ──────────────────────────────────────────
    # Chargement spaCy
    # ──────────────────────────────────────────

    def _load_spacy(self):
        try:
            import spacy
            for model in ("fr_core_news_md", "fr_core_news_sm", "fr_core_news_lg"):
                try:
                    self.nlp = spacy.load(model)
                    print(f"[spaCy] Modèle chargé : {model}", file=sys.stderr)
                    return
                except OSError:
                    continue
            print(
                "[Avertissement] Aucun modèle spaCy français trouvé.\n"
                "  NER (noms/prénoms/lieux) désactivé.\n"
                "  Installez-le avec : python -m spacy download fr_core_news_md",
                file=sys.stderr,
            )
        except ImportError:
            print(
                "[Avertissement] spaCy non installé — NER désactivé.\n"
                "  pip install spacy && python -m spacy download fr_core_news_md",
                file=sys.stderr,
            )

    # ──────────────────────────────────────────
    # Gestion du mapping
    # ──────────────────────────────────────────

    def _placeholder(self, category: str, value: str) -> str:
        """Retourne un marqueur stable pour une valeur donnée."""
        if value in self.mapping:
            return self.mapping[value]
        self.counters[category] = self.counters.get(category, 0) + 1
        tag = f"[{category}_{self.counters[category]}]"
        self.mapping[value] = tag
        self.reverse_mapping[tag] = value
        return tag

    def save_mapping(self, filepath: str):
        """Sauvegarde le mapping pour une dé-anonymisation ultérieure."""
        data = {
            "mapping": self.mapping,
            "reverse_mapping": self.reverse_mapping,
            "counters": self.counters,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Mapping] Sauvegardé dans : {filepath}", file=sys.stderr)

    def _load_mapping(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.mapping = data.get("mapping", {})
        self.reverse_mapping = data.get("reverse_mapping", {})
        self.counters = data.get("counters", {})
        print(f"[Mapping] Chargé depuis : {filepath}", file=sys.stderr)

    # ──────────────────────────────────────────
    # Anonymisation par regex
    # ──────────────────────────────────────────

    def _regex_replace(self, text: str, pattern: re.Pattern, category: str) -> str:
        validator = VALIDATORS.get(category)

        def _sub(m):
            value = m.group()
            if validator and not validator(value):
                return value  # faux positif → on laisse intact
            return self._placeholder(category, value)
        return pattern.sub(_sub, text)

    def _anonymize_ports(self, text: str) -> str:
        """Remplace les ports mentionnés avec un mot-clé (port: 8080)."""
        def _sub(m):
            prefix = m.group(1)
            port = m.group(2)
            return prefix + self._placeholder("PORT", port)
        return PATTERNS["PORT_KEYWORD"].sub(_sub, text)

    def _anonymize_regex(self, text: str) -> str:
        # MAC avant IPv6 — sinon "00:1A:2B:3C:4D:5E" matché comme IPv6
        order = [
            ("PAN",          "CB"),
            ("NIR",          "NIR"),
            ("IBAN",         "IBAN"),
            ("EMAIL",        "EMAIL"),
            ("MAC",          "MAC"),
            ("IPv6",         "IPv6"),
            ("IPv4",         "IPv4"),
            ("TEL_FR",       "TEL"),
            ("HOSTNAME",     "HOSTNAME"),
            ("CP_FR",        "CODE_POSTAL"),
        ]
        for key, category in order:
            text = self._regex_replace(text, PATTERNS[key], category)
        text = self._anonymize_ports(text)
        return text

    # ──────────────────────────────────────────
    # Anonymisation NER (spaCy)
    # ──────────────────────────────────────────

    def _anonymize_ner(self, text: str) -> str:
        if self.nlp is None:
            return text

        doc = self.nlp(text)
        label_map = {
            "PER":  "PERSONNE",
            "ORG":  "ORGANISATION",
            "LOC":  "LIEU",
            "GPE":  "LIEU",
            "MISC": "DIVERS",
        }
        entities = [
            (ent.start_char, ent.end_char, label_map.get(ent.label_, ent.label_), ent.text)
            for ent in doc.ents
            if ent.label_ in label_map
        ]
        # Remplacement en ordre inverse pour préserver les offsets
        for start, end, category, ent_text in sorted(entities, key=lambda x: x[0], reverse=True):
            tag = self._placeholder(category, ent_text)
            text = text[:start] + tag + text[end:]
        return text

    # ──────────────────────────────────────────
    # API publique
    # ──────────────────────────────────────────

    def anonymize(self, text: str) -> str:
        """Anonymise toutes les données sensibles dans le texte."""
        text = self._anonymize_regex(text)
        text = self._anonymize_ner(text)
        return text

    def deanonymize(self, text: str) -> str:
        """Restaure le texte original à partir du mapping."""
        for tag, original in self.reverse_mapping.items():
            text = text.replace(tag, original)
        return text

    def summary(self) -> str:
        """Retourne un résumé des éléments anonymisés."""
        if not self.mapping:
            return "Aucune donnée sensible détectée."
        lines = ["Données anonymisées :"]
        for original, tag in sorted(self.mapping.items(), key=lambda x: x[1]):
            lines.append(f"  {tag:<30} ← {original!r}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anonymizer",
        description="Anonymise les données sensibles avant soumission à un outil IA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  # Depuis stdin
  echo "Contacter Jean Dupont à jean.dupont@acme.fr" | python anonymizer.py

  # Fichier en entrée / sortie
  python anonymizer.py -i rapport.txt -o rapport_anon.txt

  # Sauvegarder le mapping (pour dé-anonymiser plus tard)
  python anonymizer.py -i rapport.txt -o rapport_anon.txt --save-mapping mapping.json

  # Afficher le résumé des remplacements
  python anonymizer.py -i rapport.txt --summary

  # Dé-anonymiser (récupérer le texte original)
  python anonymizer.py --deanonymize -i rapport_anon.txt --load-mapping mapping.json

  # Mode interactif (saisie manuelle)
  python anonymizer.py --interactive
        """,
    )
    parser.add_argument("-i", "--input",  help="Fichier d'entrée  (défaut : stdin)")
    parser.add_argument("-o", "--output", help="Fichier de sortie (défaut : stdout)")
    parser.add_argument("--deanonymize",  action="store_true", help="Mode dé-anonymisation")
    parser.add_argument("--save-mapping", metavar="FILE", help="Sauvegarder le mapping JSON")
    parser.add_argument("--load-mapping", metavar="FILE", help="Charger un mapping JSON existant")
    parser.add_argument("--summary",      action="store_true", help="Afficher les remplacements effectués")
    parser.add_argument("--interactive",  action="store_true", help="Mode interactif (saisie ligne par ligne)")
    return parser


def interactive_mode(anonymizer: Anonymizer):
    print("Mode interactif — Collez votre texte puis appuyez sur Entrée + Ctrl+D (Linux/Mac) ou Ctrl+Z+Entrée (Windows).")
    print("Tapez 'exit' pour quitter.\n")
    while True:
        try:
            lines = []
            while True:
                line = input()
                if line.lower() == "exit":
                    return
                lines.append(line)
        except EOFError:
            pass

        if not lines:
            continue

        text = "\n".join(lines)
        result = anonymizer.anonymize(text)
        print("\n─── Texte anonymisé ───")
        print(result)
        print("───────────────────────\n")
        print(anonymizer.summary())
        print()


def main():
    parser = build_parser()
    args = parser.parse_args()

    anonymizer = Anonymizer(mapping_file=args.load_mapping)

    # ── Mode interactif ────────────────────────
    if args.interactive:
        interactive_mode(anonymizer)
        return

    # ── Lecture ───────────────────────────────
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("Entrez le texte à anonymiser (Ctrl+D pour terminer) :", file=sys.stderr)
        text = sys.stdin.read()

    # ── Traitement ────────────────────────────
    if args.deanonymize:
        result = anonymizer.deanonymize(text)
    else:
        result = anonymizer.anonymize(text)

    # ── Écriture ──────────────────────────────
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"[OK] Résultat écrit dans : {args.output}", file=sys.stderr)
    else:
        print(result)

    # ── Optionnels ────────────────────────────
    if args.save_mapping:
        anonymizer.save_mapping(args.save_mapping)

    if args.summary:
        print("\n" + anonymizer.summary(), file=sys.stderr)


if __name__ == "__main__":
    main()
