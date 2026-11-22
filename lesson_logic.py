"""Dars mantiqi (Kivy'ga bog'liq emas, alohida sinash va tekshirish mumkin).

1) Tartib: so'z o'rgatiladi, misol esa faqat undagi barcha so'zlar o'rgatilgandan
   keyin so'raladi. Misoldagi so'zlar inglizcha matn bo'yicha aniqlanadi.
2) Javob tekshirish: katta-kichik harf, vergul, nuqta va boshqa tinish belgilari
   e'tiborga olinmaydi (General IELTS darajasi). "I'm" = "I am" ham qabul qilinadi.
3) Takroriy misollar o'zgarishsiz qoldiriladi (YouTube darsdagidek).
"""
import re

_CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "shan't": "shall not",
    "i'm": "i am", "you're": "you are", "we're": "we are", "they're": "they are",
    "he's": "he is", "she's": "she is", "it's": "it is", "that's": "that is",
    "there's": "there is", "here's": "here is", "what's": "what is",
    "who's": "who is", "where's": "where is", "let's": "let us",
    "i've": "i have", "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "he'll": "he will", "she'll": "she will",
    "we'll": "we will", "they'll": "they will", "it'll": "it will",
    "i'd": "i would", "you'd": "you would", "he'd": "he would", "she'd": "she would",
    "we'd": "we would", "they'd": "they would",
}


def clean_text(text):
    """Taqqoslash uchun: kichik harf, tinish belgisiz, qisqartmalar yoyilgan."""
    text = (text or "").lower()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("ʼ", "'")
    for short, full in _CONTRACTIONS.items():
        text = re.sub(r"(?<![\w'])" + re.escape(short) + r"(?![\w'])", full, text)
    text = re.sub(r"(\w)n't\b", r"\1 not", text)           # isn't, don't, doesn't ...
    text = re.sub(r"[^\w\s]", " ", text)                    # tinish belgilar -> bo'shliq
    text = re.sub(r"\bcan not\b", "cannot", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _token_matches(token, base):
    """'friend' so'zi 'friends' yoki 'walked' kabi shakllarga ham mos kelsin."""
    if token == base:
        return True
    if len(base) < 3:          # 'a', 'is', 'to' kabi qisqa so'zlarga qo'shimcha shakl yo'q
        return False
    variants = {base + 's', base + 'es', base + 'ed', base + 'd', base + 'ing'}
    if base.endswith('y'):
        variants.add(base[:-1] + 'ies')
        variants.add(base[:-1] + 'ied')
    if base.endswith('e'):
        variants.add(base[:-1] + 'ing')
    return token in variants


def phrase_in(phrase, tokens):
    """phrase (so'zlar ro'yxati) tokens ichida ketma-ket uchraydimi."""
    n = len(phrase)
    if n == 0 or n > len(tokens):
        return False
    for start in range(len(tokens) - n + 1):
        if tokens[start:start + n - 1] == phrase[:-1] and _token_matches(tokens[start + n - 1], phrase[-1]):
            return True
    return False


# Egalik so'zlari: o'zbekchada qo'shimcha bilan keladi ("do'stim" = my friend).
# Gapda alohida "mening/sening" bo'lmasa, inglizcha "my/your" alohida o'rgatilishi kutilmaydi.
_POSSESSIVE_UZ = {
    ("my",): {"mening"},
    ("your",): {"sening", "sizning"},
    ("his",): {"uning"},
    ("her",): {"uning"},
}


def needs_word(phrase, example):
    """Misol uchun shu so'z (ibora) alohida o'rgatilgan bo'lishi shartmi."""
    uz_needed = _POSSESSIVE_UZ.get(tuple(phrase))
    if uz_needed is not None:
        return bool(uz_needed & set(clean_text(example['uz']).split()))
    return True


def build_steps(lesson):
    """Dars bosqichlari ro'yxati.

    ('word', so'z_indeksi)  yoki  ('example', misol_lug'ati, egasi_indeksi)
    Har bir misol aynan bir marta, o'zidagi barcha so'zlar o'rgatilgandan keyin so'raladi.
    """
    words = lesson['words']
    phrases = [clean_text(w['en']).split() for w in words]

    pool = []
    for owner, w in enumerate(words):
        for ex in w.get('examples', []):
            tokens = clean_text(ex['en']).split()
            ready = owner  # misol o'z so'zidan oldin so'ralmaydi
            for j, phrase in enumerate(phrases):
                if j > ready and phrase_in(phrase, tokens) and needs_word(phrase, ex):
                    ready = j
            pool.append((ready, ex))

    steps = []
    asked = [False] * len(pool)
    for i in range(len(words)):
        steps.append(('word', i))
        for k, (ready, ex) in enumerate(pool):
            if not asked[k] and ready <= i:
                steps.append(('example', ex, i))
                asked[k] = True
    return steps


def accepted_answers(lesson, example):
    """Misol uchun qabul qilinadigan barcha javoblar (tozalangan holda).

    - Shu darsda bir xil o'zbekcha gapga boshqacha inglizcha javob yozilgan bo'lsa,
      u ham to'g'ri hisoblanadi (masalan "Help, please." va "Please help.").
    - "dadam", "do'stim" kabi egalik qo'shimchali so'zlar: "Hello, dad." ga
      "Hello, my dad." deb yozish ham to'g'ri.
    """
    target_uz = clean_text(example['uz'])
    accepted = {clean_text(example['en'])}
    for w in lesson['words']:
        for e in w.get('examples', []):
            if clean_text(e['uz']) == target_uz:
                accepted.add(clean_text(e['en']))

    uz_tokens = target_uz.split()
    for uz_word, en_word in (("dadam", "dad"), ("onam", "mom")):
        if uz_word in uz_tokens:
            for ans in list(accepted):
                tokens = ans.split()
                if en_word in tokens:
                    i = tokens.index(en_word)
                    if i == 0 or tokens[i - 1] not in ("my", "your", "his", "her", "our", "their"):
                        accepted.add(" ".join(tokens[:i] + ["my"] + tokens[i:]))
    return accepted


def is_correct(lesson, example, user_answer):
    return clean_text(user_answer) in accepted_answers(lesson, example)
