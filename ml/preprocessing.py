import re

PAD_ID = 0
OOV_ID = 1

MAX_SEQUENCE_LENGTH = 8
MAX_VOCAB_SIZE = 128


def tokenize(text: str) -> list:
    """Convert text into deterministic lowercase tokens."""
    return re.findall(r"\b[\w'-]+\b", text.lower())


def build_vocabulary(texts: list[str]) -> dict[str, int]:
    """
    Build the vocabulary from training data only.

    0 is reserved for PAD (Padding).
    1 is reserved for OOV (Out Of Vocabulary).
    """
    word_counts: dict[str, int] = {}

    for text in texts:
        for token in tokenize(text):
            word_counts[token] = word_counts.get(token, 0) + 1

    # Ordering: most frequent first, alphabetical for equal frequencies
    sorted_words = sorted(
        word_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    # Two IDs are already reserved.
    available_words = MAX_VOCAB_SIZE - 2

    vocabulary = {
        word: index + 2
        for index, (word, _) in enumerate(sorted_words[:available_words])
    }

    return vocabulary


def encode_text(text: str, vocabulary: dict[str, int]) -> list[int]:
    tokens = tokenize(text)

    token_ids = [vocabulary.get(token, OOV_ID) for token in tokens]

    token_ids = token_ids[:MAX_SEQUENCE_LENGTH]

    padding_required = MAX_SEQUENCE_LENGTH - len(token_ids)

    token_ids.extend([PAD_ID] * padding_required)

    return token_ids
