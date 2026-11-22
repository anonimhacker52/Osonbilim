"""Darslar JSON fayllarini tekshiradi. Ishga tushirish (repo papkasida):

    python tools/validate_lessons.py            # hamma darslar
    python tools/validate_lessons.py 12-dars    # bitta dars

XATO  = ilova ishlamay qolishi yoki noto'g'ri ishlashi mumkin (tuzatish kerak).
OGOH  = o'quvchiga qiyin bo'lishi mumkin; ilova baribir ishlaydi (qaror sizniki).
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lesson_logic import clean_text, phrase_in, needs_word, _token_matches  # noqa: E402


def lesson_num(path):
    m = re.match(r"(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 10 ** 9


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = sorted(glob.glob(os.path.join(ROOT, "darslar", "*.json")), key=lesson_num)
    errors = warns = 0
    known = set()          # oldingi darslarda o'tilgan inglizcha so'zlar

    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        out = []

        def err(msg):
            nonlocal errors
            errors += 1
            out.append("  XATO  " + msg)

        def warn(msg):
            nonlocal warns
            warns += 1
            out.append("  OGOH  " + msg)

        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            data = json.loads(text)
        except ValueError as e:
            print(f"{name}: XATO  JSON noto'g'ri yozilgan: {e}")
            errors += 1
            continue

        # Ko'rinmas/boshqa alifbo harflari (masalan kirill harfi lotin "a" o'rniga)
        for ln, line in enumerate(text.splitlines(), 1):
            bad = re.findall(r"[Ѐ-ӿ ​﻿]", line)
            if bad:
                err(f"{ln}-qator: kirill yoki ko'rinmas belgi bor: {line.strip()[:70]}")

        if not data.get("title"):
            err("title yo'q")
        words = data.get("words")
        if not isinstance(words, list) or not words:
            print(f"{name}: XATO  words ro'yxati yo'q yoki bo'sh")
            errors += 1
            continue
        if not data.get("story") or not data["story"].get("text"):
            warn("hikoya (story) yo'q")

        phrases = [clean_text(w.get("en", "")).split() for w in words]
        for i, w in enumerate(words):
            tag = f"{i + 1}-so'z"
            if not w.get("uz") or not w.get("en"):
                err(f"{tag}: uz yoki en bo'sh")
                continue
            if re.search(r"[/;]", w["uz"] + w["en"]):
                warn(f"{tag} '{w['uz']} = {w['en']}': '/' belgisi bor")
            if not w.get("examples"):
                warn(f"{tag} '{w['en']}': misollar yo'q")
            for k, e in enumerate(w.get("examples", []), 1):
                if not e.get("uz") or not e.get("en"):
                    err(f"{tag} {k}-misol: uz yoki en bo'sh")
                    continue
                toks = clean_text(e["en"]).split()
                if not toks:
                    err(f"{tag} {k}-misol: inglizcha matn bo'sh")
                    continue
                if e["uz"].strip() == e["en"].strip():
                    warn(f"{tag} {k}-misol: uz va en bir xil: {e['en']}")
                # Ilova bunday misolni kerakli so'z o'rgatilgandan keyin so'raydi (xato emas)
                later = [words[j]["en"] for j in range(i + 1, len(words))
                         if phrases[j] and phrase_in(phrases[j], toks) and needs_word(phrases[j], e)]
                if later:
                    out.append(f"  ESLATMA {tag} '{w['en']}' misoli \"{e['en']}\" "
                               f"{', '.join(later)} so'zini kutadi (ilova o'zi tartiblaydi)")
                # Hech bir darsda o'rgatilmagan so'z
                mine = set(sum(phrases, [])) | known
                unk = [t for t in toks if not any(_token_matches(t, k2) for k2 in mine)]
                if unk:
                    warn(f"{tag} \"{e['en']}\": o'tilmagan so'z: {', '.join(unk)}")

        story = (data.get("story") or {}).get("text", "")
        mine = set(sum(phrases, [])) | known
        unk = sorted({t for t in clean_text(story).split()
                      if not any(_token_matches(t, k2) for k2 in mine)})
        if unk:
            warn(f"hikoyada o'tilmagan so'zlar: {', '.join(unk)}")

        known |= set(sum(phrases, []))
        if only and only != name:
            continue
        status = "OK" if not any(l.startswith("  XATO") for l in out) else "XATO bor"
        print(f"{name}: {len(words)} so'z, {sum(len(w.get('examples', [])) for w in words)} misol - {status}")
        for line in out:
            print(line)

    print(f"\nJami: {errors} ta XATO, {warns} ta OGOH")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
