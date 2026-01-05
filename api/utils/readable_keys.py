"""
Human-Readable Keys for Collective Memory
==========================================
Format: {adjective}-{adjective}-{adjective}-{noun}
All words: 4-7 letters
Combinations: 500 × 500 × 500 × 1000 = 125 billion unique keys

Examples:
  swift-bold-keen-lion
  calm-fresh-wild-river
  bright-quick-warm-spark
"""

import random
from typing import Optional, Set, Callable

# 500 Adjectives and Verbs (4-7 letters, A-Z)
ADJECTIVES_VERBS = [
    # A (20)
    "able", "acid", "aged", "airy", "alert",
    "alive", "amber", "ample", "angry", "apart",
    "avid", "awake", "azure", "agile", "acute",
    "adrift", "aerial", "alpine", "arcane", "arched",
    # B (20)
    "bald", "bare", "base", "bold", "brave",
    "brief", "brisk", "broad", "blunt", "burnt",
    "bushy", "balmy", "bland", "bleak", "blithe",
    "bonded", "brainy", "brassy", "brazen", "bright",
    # C (20)
    "calm", "cold", "cool", "cozy", "curt",
    "cheap", "chief", "civil", "clean", "clear",
    "close", "crisp", "cross", "crude", "curly",
    "candid", "casual", "clever", "cloudy", "cosmic",
    # D (20)
    "damp", "dark", "dead", "deaf", "dear",
    "deep", "deft", "dire", "dull", "dense",
    "dirty", "dizzy", "dopey", "dried", "dusty",
    "dapper", "daring", "decent", "devout", "dreamy",
    # E (20)
    "each", "easy", "edgy", "even", "evil",
    "eager", "early", "eerie", "elite", "empty",
    "equal", "exact", "extra", "earthy", "elated",
    "expert", "exotic", "ethnic", "entire", "errant",
    # F (20)
    "fair", "fake", "fast", "fine", "firm",
    "flat", "fond", "foul", "free", "full",
    "faded", "faint", "false", "fancy", "fatal",
    "fiery", "final", "fixed", "fleet", "foggy",
    # G (20)
    "game", "gilt", "glad", "gold", "good",
    "gray", "grim", "gaudy", "gaunt", "giant",
    "giddy", "given", "grand", "grave", "great",
    "green", "grimy", "gross", "golden", "gothic",
    # H (20)
    "hale", "half", "hard", "hazy", "high",
    "holy", "hairy", "handy", "happy", "hardy",
    "harsh", "hasty", "heavy", "hefty", "hilly",
    "huffy", "humid", "husky", "hidden", "hollow",
    # I (20)
    "iced", "idle", "iffy", "inner", "ionic",
    "irate", "itchy", "ivory", "ideal", "inert",
    "inked", "input", "irked", "island", "italic",
    "inland", "innate", "intent", "inward", "ironic",
    # J (20)
    "just", "jaded", "jazzy", "jerky", "joint",
    "jolly", "juicy", "jumbo", "jumpy", "junky",
    "jaunty", "jested", "jolted", "jovial", "joyful",
    "joyous", "junior", "jiggly", "jingly", "jutted",
    # K (20)
    "keen", "kept", "kind", "known", "kooky",
    "khaki", "kinky", "kindly", "kingly", "knotty",
    "kosher", "keyed", "kempt", "kicked", "killed",
    "kissed", "kitted", "knifed", "knurly", "krispy",
    # L (20)
    "lame", "last", "late", "lazy", "lean",
    "left", "less", "limp", "live", "lone",
    "long", "lost", "loud", "lush", "lanky",
    "large", "leafy", "legal", "level", "light",
    # M (20)
    "made", "main", "male", "mass", "meek",
    "mere", "mild", "mint", "moot", "much",
    "mute", "magic", "major", "manic", "merry",
    "messy", "metal", "milky", "minor", "misty",
    # N (20)
    "near", "neat", "next", "nice", "nine",
    "numb", "naive", "naked", "nasty", "naval",
    "nervy", "newly", "ninth", "noble", "noisy",
    "north", "noted", "nutty", "narrow", "native",
    # O (20)
    "oaky", "oily", "okay", "only", "open",
    "oral", "ours", "oval", "over", "owed",
    "ocean", "oddly", "olive", "other", "outer",
    "owing", "owned", "obtuse", "opaque", "ornate",
    # P (20)
    "paid", "pale", "past", "pink", "plus",
    "poor", "posh", "pure", "plaid", "plain",
    "plump", "polar", "prime", "prior", "prone",
    "proud", "petty", "pious", "placid", "poised",
    # Q (10)
    "quick", "quiet", "quite", "quaint", "quoted",
    "queued", "quirky", "quaked", "quasi", "queen",
    # R (20)
    "rare", "rash", "real", "rear", "rich",
    "rife", "ripe", "rosy", "rude", "rapid",
    "ready", "rigid", "risky", "rocky", "rough",
    "round", "royal", "ruled", "rural", "rusty",
    # S (20)
    "safe", "sage", "same", "sane", "slim",
    "slow", "smug", "snug", "soft", "sole",
    "some", "sore", "sour", "sure", "sharp",
    "shiny", "short", "silky", "simple", "sleepy",
    # T (20)
    "tame", "tall", "tart", "taut", "thin",
    "tidy", "tiny", "torn", "trim", "true",
    "taken", "tepid", "thick", "tight", "timid",
    "tired", "total", "tough", "toxic", "tried",
    # U (20)
    "ugly", "used", "unit", "ultra", "uncut",
    "under", "undue", "unfit", "union", "upper",
    "urban", "usual", "utter", "upbeat", "uphill",
    "upload", "upward", "urgent", "useful", "unique",
    # V (20)
    "vain", "vast", "very", "vile", "void",
    "valid", "vapid", "velvet", "vented", "verbal",
    "versed", "vexed", "viral", "vital", "vivid",
    "vocal", "vogue", "valued", "varied", "veiled",
    # W (20)
    "warm", "wary", "wavy", "weak", "wide",
    "wild", "wily", "wise", "worn", "weary",
    "weird", "welsh", "white", "whole", "windy",
    "witty", "wobbly", "wooden", "woolly", "worthy",
    # X (6)
    "xeric", "xerox", "xylem", "xylic", "xenial", "xrayed",
    # Y (14)
    "yare", "young", "yummy", "yearly", "yellow",
    "yelped", "yonder", "yawned", "yanked", "yeasty",
    "yield", "yokel", "yolked", "youthy",
    # Z (10)
    "zany", "zero", "zesty", "zincy", "zingy",
    "zippy", "zonal", "zoomed", "zenith", "zigzag",
    # Extra (20)
    "aglow", "ashen", "basic", "briny", "coral",
    "dingy", "dusky", "feral", "fluid", "frail",
    "glum", "gruff", "gusty", "hoary", "lucid",
    "murky", "plush", "stark", "swamp", "terse",
]

# 1000 Nouns (4-7 letters, A-Z)
NOUNS = [
    # A (40)
    "acre", "ally", "apex", "arch", "area",
    "army", "atom", "aunt", "axis", "baby",
    "acorn", "actor", "agent", "agony", "alarm",
    "album", "algae", "alien", "alloy", "alpha",
    "altar", "amber", "angel", "angle", "angst",
    "anvil", "apple", "arena", "argon", "aroma",
    "arrow", "asset", "atlas", "attic", "audio",
    "award", "azure", "abbey", "abyss", "adage",
    # B (40)
    "bale", "ball", "band", "bank", "barn",
    "base", "bath", "bead", "beak", "beam",
    "bean", "bear", "beat", "bell", "belt",
    "bend", "bike", "bird", "bite", "bloc",
    "boat", "body", "bolt", "bomb", "bond",
    "bone", "book", "boom", "boot", "boss",
    "bowl", "brim", "bulk", "bull", "bump",
    "bush", "byte", "badge", "baker", "baron",
    # C (40)
    "cafe", "cage", "cake", "calf", "call",
    "camp", "cape", "card", "care", "cart",
    "case", "cash", "cast", "cave", "cell",
    "chef", "chip", "city", "clan", "claw",
    "clay", "clip", "club", "clue", "coal",
    "coat", "code", "coil", "coin", "colt",
    "cone", "cook", "cope", "cord", "core",
    "cork", "corn", "cost", "coup", "crab",
    # D (40)
    "dame", "data", "dawn", "deal", "dean",
    "debt", "deck", "deed", "deer", "demo",
    "dent", "desk", "dial", "dice", "diet",
    "dirt", "disc", "dish", "disk", "dock",
    "dome", "door", "dose", "dove", "down",
    "draw", "drop", "drum", "duck", "duel",
    "duke", "dune", "dust", "duty", "decal",
    "decor", "decoy", "deity", "delta", "demon",
    # E (40)
    "earl", "ease", "east", "echo", "edge",
    "envy", "epic", "exam", "exit", "expo",
    "eagle", "earth", "ember", "emcee", "enemy",
    "entry", "envoy", "epoch", "equal", "equip",
    "error", "essay", "ether", "event", "exile",
    "email", "empty", "ended", "enjoy", "enter",
    "erupt", "evade", "exact", "exalt", "excel",
    "exert", "expat", "extra", "eying", "elbow",
    # F (40)
    "face", "fact", "fade", "fail", "fair",
    "fall", "fame", "fang", "farm", "fate",
    "fawn", "fear", "feat", "feed", "feel",
    "feet", "fern", "file", "film", "find",
    "fire", "firm", "fish", "fist", "flag",
    "flat", "flaw", "flex", "flip", "flow",
    "flux", "foam", "fold", "folk", "font",
    "food", "fool", "foot", "ford", "fork",
    # G (40)
    "gait", "gale", "game", "gang", "gate",
    "gaze", "gear", "gene", "gift", "girl",
    "gist", "glen", "glow", "glue", "goal",
    "goat", "gold", "golf", "gong", "good",
    "gown", "grab", "gram", "grid", "grin",
    "grip", "grit", "grow", "gulf", "guru",
    "gust", "ghost", "giant", "gland", "glass",
    "gleam", "gloom", "glory", "gnome", "grace",
    # H (40)
    "hail", "hair", "hake", "half", "hall",
    "halo", "halt", "hand", "hang", "hare",
    "harm", "harp", "hate", "hawk", "haze",
    "head", "heal", "heap", "heat", "heed",
    "heel", "heir", "held", "helm", "help",
    "herb", "herd", "hero", "hide", "hill",
    "hint", "hive", "hoard", "hobby", "homer",
    "honey", "honor", "horse", "hotel", "hound",
    # I (40)
    "ibex", "icon", "idea", "idol", "inch",
    "info", "iris", "iron", "isle", "item",
    "ivory", "image", "inbox", "index", "input",
    "intel", "intro", "inlay", "inlet", "inner",
    "issue", "igloo", "impel", "imply", "incur",
    "inept", "infer", "ingot", "inked", "iotas",
    "ionic", "irate", "irked", "irony", "ivied",
    "icing", "ideal", "idiom", "idler", "ileum",
    # J (40)
    "jack", "jade", "jail", "jake", "jamb",
    "jape", "java", "jazz", "jean", "jeer",
    "jelly", "jerky", "jewel", "jiffy", "jingo",
    "jiver", "joker", "jolly", "joust", "joule",
    "judge", "juice", "jumbo", "jumps", "juror",
    "jaunt", "jeans", "jenny", "jetty", "jests",
    "joint", "jolts", "jowls", "jumpy", "junco",
    "junta", "jutty", "jambs", "japes", "jarred",
    # K (30)
    "kale", "kelp", "keys", "kick", "kill",
    "kilt", "kind", "king", "kink", "kiosk",
    "kite", "knack", "knead", "kneed", "kneel",
    "knife", "knobs", "knock", "knoll", "knots",
    "kayak", "kebab", "keeps", "khaki", "kiddo",
    "kinky", "ketch", "kitty", "klutz", "knave",
    # L (40)
    "lace", "lack", "lady", "lair", "lake",
    "lamb", "lamp", "land", "lane", "lard",
    "lark", "lash", "last", "late", "lava",
    "lawn", "lead", "leaf", "leak", "leap",
    "lens", "liar", "lice", "life", "lift",
    "limb", "lime", "limp", "line", "link",
    "lion", "list", "live", "load", "loaf",
    "loan", "lobe", "lock", "loft", "logo",
    # M (40)
    "mace", "made", "maid", "mail", "main",
    "make", "male", "mall", "mane", "many",
    "mare", "mark", "mars", "mask", "mass",
    "mast", "mate", "math", "maze", "meal",
    "mean", "meat", "meek", "meet", "memo",
    "menu", "mesa", "mesh", "mess", "mica",
    "mice", "mild", "mile", "milk", "mill",
    "mime", "mind", "mine", "mint", "mist",
    # N (40)
    "nail", "name", "nape", "navy", "near",
    "neat", "neck", "need", "neon", "nerd",
    "nest", "news", "next", "nice", "nick",
    "nine", "node", "noel", "none", "noon",
    "norm", "nose", "note", "noun", "nova",
    "nudge", "nylon", "nymph", "nadir", "nasal",
    "navel", "nerve", "never", "nexus", "niche",
    "night", "ninja", "noble", "noise", "notch",
    # O (40)
    "oath", "odds", "odor", "oils", "okay",
    "omen", "only", "onto", "opal", "open",
    "opts", "oral", "orbs", "orca", "ores",
    "ounce", "outdo", "outer", "ovary", "overt",
    "owner", "oxide", "ozone", "ocean", "octet",
    "offer", "often", "olive", "omega", "onion",
    "onset", "opera", "optic", "orbit", "order",
    "organ", "other", "otter", "ought", "outgo",
    # P (40)
    "pace", "pack", "pact", "page", "paid",
    "pail", "pain", "pair", "pale", "palm",
    "pane", "park", "part", "pass", "past",
    "path", "pawn", "peak", "pear", "peas",
    "peat", "peel", "peer", "perk", "pest",
    "pier", "pike", "pile", "pine", "pink",
    "pint", "pipe", "pith", "plan", "play",
    "plea", "plot", "plow", "plug", "plum",
    # Q (20)
    "quad", "quay", "query", "quest", "queue",
    "quick", "quiet", "quill", "quilt", "quirk",
    "quota", "quote", "qualm", "quark", "quart",
    "queen", "queer", "quench", "quiche", "quid",
    # R (40)
    "race", "rack", "raft", "rage", "raid",
    "rail", "rain", "rake", "ramp", "rang",
    "rank", "rant", "rate", "rave", "rays",
    "read", "real", "ream", "rear", "reed",
    "reef", "reel", "rent", "rest", "rice",
    "ride", "rift", "ring", "riot", "rise",
    "risk", "rite", "road", "roam", "robe",
    "rock", "rode", "role", "roll", "roof",
    # S (40)
    "sack", "safe", "sage", "sail", "sake",
    "sale", "salt", "sand", "sash", "seal",
    "seam", "seat", "sect", "seed", "self",
    "shed", "ship", "shop", "shot", "show",
    "side", "sigh", "sign", "silk", "sink",
    "site", "size", "skin", "slab", "slam",
    "slap", "sled", "slew", "slim", "slip",
    "slob", "slot", "slow", "slug", "snap",
    # T (40)
    "tack", "tail", "take", "tale", "talk",
    "tall", "tank", "tape", "task", "team",
    "tear", "teen", "tell", "temp", "tent",
    "term", "test", "text", "than", "that",
    "them", "then", "tide", "tile", "till",
    "time", "tint", "tire", "toad", "toll",
    "tomb", "tone", "tool", "toot", "tops",
    "tore", "torn", "tour", "town", "trap",
    # U (30)
    "uber", "ughs", "ugly", "undo", "unit",
    "unto", "upon", "urge", "urea", "user",
    "udder", "ulcer", "ultra", "umbra", "uncle",
    "under", "undue", "union", "unite", "unity",
    "until", "upper", "upset", "urban", "urged",
    "urine", "usage", "usher", "usual", "utter",
    # V (30)
    "vain", "vale", "vamp", "vane", "vary",
    "vase", "vast", "veal", "veer", "veil",
    "vein", "vent", "verb", "very", "vest",
    "veto", "vibe", "vice", "vida", "view",
    "vigor", "villa", "vinyl", "viola", "viper",
    "viral", "virus", "visor", "visit", "vista",
    # W (40)
    "wade", "wage", "wail", "wait", "wake",
    "walk", "wall", "wand", "want", "ward",
    "warm", "warn", "warp", "wart", "wash",
    "wasp", "wave", "wavy", "waxy", "weak",
    "wean", "wear", "weed", "week", "well",
    "west", "what", "when", "whey", "whim",
    "whip", "wick", "wide", "wife", "wild",
    "will", "wilt", "wind", "wine", "wing",
    # X (10)
    "xbox", "xmas", "xray", "xerox", "xylem",
    "xenon", "xeric", "xylan", "xylon", "xysts",
    # Y (20)
    "yams", "yang", "yank", "yard", "yarn",
    "yawn", "year", "yell", "yelp", "yoga",
    "yoke", "yolk", "your", "youth", "yacht",
    "yearn", "yeast", "yield", "yodel", "yokel",
    # Z (20)
    "zany", "zaps", "zeal", "zebu", "zero",
    "zest", "zinc", "zing", "zone", "zoom",
    "zebra", "zesty", "zilch", "zincs", "zings",
    "zippy", "zonal", "zones", "zooms", "zowie",
    # Extra (80)
    "abode", "adder", "aisle", "ankle", "armor",
    "bacon", "batch", "beard", "beast", "birch",
    "blade", "blank", "blaze", "blend", "blink",
    "bloom", "bluff", "board", "boots", "bough",
    "brain", "brand", "brass", "brick", "brink",
    "brush", "camel", "canal", "candy", "cargo",
    "chain", "chalk", "charm", "chase", "chess",
    "child", "chord", "claim", "clamp", "clash",
    "class", "cliff", "climb", "cloak", "clock",
    "coach", "coast", "coral", "couch", "court",
    "craft", "crane", "crash", "crawl", "cream",
    "creek", "crest", "crisp", "crown", "crust",
    "diary", "ditch", "diver", "dodge", "donor",
    "draft", "drain", "drama", "drape", "dread",
    "dream", "dress", "drift", "drill", "drink",
    "dwarf", "dwell", "easel", "evict", "extol",
]


def generate_readable_key(existing_keys: Optional[Set[str]] = None) -> str:
    """
    Generate a human-readable key in format: adj-adj-adj-noun

    Args:
        existing_keys: Optional set of existing keys to avoid collisions

    Returns:
        A unique human-readable key
    """
    max_attempts = 100

    for _ in range(max_attempts):
        key = "-".join([
            random.choice(ADJECTIVES_VERBS),
            random.choice(ADJECTIVES_VERBS),
            random.choice(ADJECTIVES_VERBS),
            random.choice(NOUNS),
        ])

        if existing_keys is None or key not in existing_keys:
            return key

    # Fallback: append random suffix
    base = "-".join([
        random.choice(ADJECTIVES_VERBS),
        random.choice(ADJECTIVES_VERBS),
        random.choice(ADJECTIVES_VERBS),
        random.choice(NOUNS),
    ])
    return f"{base}-{random.randint(1000, 9999)}"


def generate_readable_key_with_check(
    exists_fn: Callable[[str], bool],
    max_attempts: int = 100
) -> str:
    """
    Generate a human-readable key, checking for existence via callback.

    Args:
        exists_fn: Function that returns True if key already exists
        max_attempts: Maximum generation attempts before adding suffix

    Returns:
        A unique human-readable key
    """
    for _ in range(max_attempts):
        key = "-".join([
            random.choice(ADJECTIVES_VERBS),
            random.choice(ADJECTIVES_VERBS),
            random.choice(ADJECTIVES_VERBS),
            random.choice(NOUNS),
        ])

        if not exists_fn(key):
            return key

    # Fallback: append random suffix
    base = "-".join([
        random.choice(ADJECTIVES_VERBS),
        random.choice(ADJECTIVES_VERBS),
        random.choice(ADJECTIVES_VERBS),
        random.choice(NOUNS),
    ])
    return f"{base}-{random.randint(1000, 9999)}"


def is_readable_key(key: str) -> bool:
    """
    Check if a key is in human-readable format (adj-adj-adj-noun).

    Args:
        key: The key to check

    Returns:
        True if key matches readable format, False otherwise
    """
    parts = key.split("-")
    if len(parts) < 4:
        return False

    # Check if first three parts are adjectives and last is noun
    # Allow for suffix like "-1234" at the end
    if len(parts) == 4:
        return (
            parts[0] in ADJECTIVES_VERBS and
            parts[1] in ADJECTIVES_VERBS and
            parts[2] in ADJECTIVES_VERBS and
            parts[3] in NOUNS
        )
    elif len(parts) == 5 and parts[4].isdigit():
        return (
            parts[0] in ADJECTIVES_VERBS and
            parts[1] in ADJECTIVES_VERBS and
            parts[2] in ADJECTIVES_VERBS and
            parts[3] in NOUNS
        )

    return False


def is_uuid(key: str) -> bool:
    """
    Check if a key looks like a UUID.

    Args:
        key: The key to check

    Returns:
        True if key matches UUID format
    """
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, key.lower()))


def validate_word_lists() -> dict:
    """Validate both word lists for length and uniqueness."""
    results = {
        "adjectives_verbs": {"count": 0, "errors": [], "duplicates": []},
        "nouns": {"count": 0, "errors": [], "duplicates": []},
    }

    # Check adjectives/verbs
    seen = set()
    for word in ADJECTIVES_VERBS:
        if len(word) < 4 or len(word) > 7:
            results["adjectives_verbs"]["errors"].append(f"'{word}' has {len(word)} letters")
        if word.lower() in seen:
            results["adjectives_verbs"]["duplicates"].append(word)
        seen.add(word.lower())
    results["adjectives_verbs"]["count"] = len(ADJECTIVES_VERBS)

    # Check nouns
    seen = set()
    for word in NOUNS:
        if len(word) < 4 or len(word) > 7:
            results["nouns"]["errors"].append(f"'{word}' has {len(word)} letters")
        if word.lower() in seen:
            results["nouns"]["duplicates"].append(word)
        seen.add(word.lower())
    results["nouns"]["count"] = len(NOUNS)

    return results


def get_stats() -> dict:
    """Get statistics about the word lists."""
    adj_count = len(ADJECTIVES_VERBS)
    noun_count = len(NOUNS)
    total_combinations = adj_count ** 3 * noun_count

    return {
        "adjectives_verbs_count": adj_count,
        "nouns_count": noun_count,
        "total_combinations": total_combinations,
        "combinations_billions": total_combinations / 1e9,
    }


if __name__ == "__main__":
    # Validate
    results = validate_word_lists()

    print("=== Adjectives/Verbs ===")
    print(f"Count: {results['adjectives_verbs']['count']} (target: 500)")
    if results['adjectives_verbs']['errors']:
        print(f"Length errors: {results['adjectives_verbs']['errors']}")
    else:
        print("All 4-7 letters")
    if results['adjectives_verbs']['duplicates']:
        print(f"Duplicates: {results['adjectives_verbs']['duplicates']}")
    else:
        print("No duplicates")

    print("\n=== Nouns ===")
    print(f"Count: {results['nouns']['count']} (target: 1000)")
    if results['nouns']['errors']:
        print(f"Length errors: {results['nouns']['errors']}")
    else:
        print("All 4-7 letters")
    if results['nouns']['duplicates']:
        print(f"Duplicates: {results['nouns']['duplicates']}")
    else:
        print("No duplicates")

    # Generate examples
    print("\n=== Sample Keys ===")
    for _ in range(10):
        print(f"  {generate_readable_key()}")

    # Show stats
    stats = get_stats()
    print(f"\n=== Stats ===")
    print(f"Total combinations: {stats['total_combinations']:,} ({stats['combinations_billions']:.1f} billion)")
