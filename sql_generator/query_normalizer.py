import re

# Comprehensive colloquial, phonetic typo, and Indian/Local English dictionary
COLLOQUIAL_LEXICON = {
    # Typos & phonetic representations
    r"\bndstand\b": "understand",
    r"\bundrstand\b": "understand",
    r"\bcorretcly\b": "correctly",
    r"\bcorrectli\b": "correctly",
    r"\baccoding\b": "according",
    r"\bacording\b": "according",
    r"\bans\b": "answer",
    r"\bwat\b": "what",
    r"\bwht\b": "what",
    r"\bshw\b": "show",
    r"\btel\b": "tell",
    r"\bgv\b": "give",
    r"\bplz\b": "please",
    r"\bpls\b": "please",

    # Local terminology for movies
    r"\bmovi\b": "movie",
    r"\bmovis\b": "movies",
    r"\bcinema\b": "movie",
    r"\bcinemas\b": "movies",
    r"\bpicture\b": "movie",
    r"\bpictures\b": "movies",
    r"\bpadam\b": "movie",
    r"\bfilim\b": "movie",
    r"\bfilm\b": "movie",
    r"\bfilms\b": "movies",

    # Local terminology for actors / cast
    r"\bhero\b": "actor",
    r"\bheroes\b": "actors",
    r"\bheroine\b": "actor",
    r"\bheroines\b": "actors",
    r"\bstar cast\b": "actors",
    r"\bstarcast\b": "actors",
    r"\bcast list\b": "actors",
    r"\bacting people\b": "actors",
    r"\bwho acted\b": "actors",
    r"\bartist\b": "actor",
    r"\bartists\b": "actors",
    r"\bactress\b": "actor",
    r"\bactresses\b": "actors",

    # Local terminology for directors & filmmaking
    r"\bdirecter\b": "director",
    r"\bdirecters\b": "directors",
    r"\bwho directed\b": "director",
    r"\btaken by\b": "directed by",
    r"\btook by\b": "directed by",
    r"\bwho took\b": "director",
    r"\bwho made\b": "director",
    r"\bmade by\b": "directed by",
    r"\bfilmmaker\b": "director",

    # Local terminology for box office, financials & collection
    r"\bcolletion\b": "box office",
    r"\bcollecton\b": "box office",
    r"\bcollection\b": "box office",
    r"\bcollections\b": "box office",
    r"\bkamai\b": "box office",
    r"\bbusiness\b": "box office",
    r"\bearnings\b": "box office",
    r"\bgrossing\b": "box office",
    r"\bgross\b": "box office",
    r"\brevenue\b": "box office",
    r"\bcostliest\b": "highest budget",
    r"\bcostly\b": "expensive budget",
    r"\bkarcha\b": "budget",
    r"\bmoney spent\b": "budget",
    r"\bcheap\b": "low budget",

    # Local terminology for reviews & public sentiment
    r"\btalk\b": "reviews",
    r"\bpublic talk\b": "reviews",
    r"\bpublic opinion\b": "reviews",
    r"\baudience feedback\b": "reviews",
    r"\bfeedback\b": "reviews",
    r"\brevu\b": "reviews",
    r"\breviw\b": "reviews",
    r"\brating\b": "rating",
    r"\bratng\b": "rating",
    r"\braiting\b": "rating",

    # Local terminology for success & hits
    r"\bsuperhit\b": "highest rated blockbuster",
    r"\bsuper hit\b": "highest rated blockbuster",
    r"\bblockbuster\b": "blockbuster",
    r"\bhit cinema\b": "top rated movie",
    r"\bhit movie\b": "top rated movie",
    r"\bhit\b": "top rated",

    # Runtime & length
    r"\blenghty\b": "lengthy",
    r"\blong time\b": "lengthy duration",
    r"\brun time\b": "duration",
    r"\bruntime\b": "duration",
    r"\brunning time\b": "duration",
    r"\bshort time\b": "short duration",

    # Streaming / OTT
    r"\bott\b": "streaming platform",
    r"\bott platform\b": "streaming platform",

    # Oscars & awards
    r"\bawards\b": "oscars",
    r"\baward\b": "oscar",
    r"\btrophy\b": "oscar",
    r"\btrophies\b": "oscars",
    r"\bacadeny award\b": "oscar",
    r"\bacadeny awards\b": "oscars",
    r"\bacademy award\b": "oscar",
    r"\bacademy awards\b": "oscars",

    # Birth year & age
    r"\bdob\b": "birth year",
    r"\bborn year\b": "birth year",
    r"\byear of birth\b": "birth year",
    r"\bborn in year\b": "birth year",
    r"\bborn on year\b": "birth year",
    r"\bborn on the year\b": "birth year",

    # Release phrasing
    r"\brelised\b": "released",
    r"\brelesed\b": "released",
    r"\bcame out\b": "released",
    r"\blaunched\b": "released"
}

def normalize_colloquial_query(text: str) -> str:
    """
    Normalizes colloquial English, Indian English phrasing, slang, typos,
    and phonetic variations into canonical schema terms for NLP & Text-to-SQL.
    """
    if not text:
        return ""

    normalized = text.strip()
    
    # Lowercase for replacement while preserving numbers and words
    lowered = normalized.lower()

    for pattern, replacement in COLLOQUIAL_LEXICON.items():
        lowered = re.sub(pattern, replacement, lowered, flags=re.IGNORECASE)

    # Clean up multi-spaces
    lowered = re.sub(r'\s+', ' ', lowered).strip()
    return lowered
