"""
Shared text preprocessing utilities for AI and LLM services.
Implements dynamic sampling strategies based on document length.
"""
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def _importance_sample(text: str, max_words: int) -> str:
    """
    Sample text by sentence importance scoring for very long documents.

    Scores sentences based on:
    - Financial keywords (revenue, earnings, profit, etc.)
    - Entity keywords (company names, inc, corp, etc.)
    - Action keywords (announced, reported, filed, etc.)
    - Numeric data (financial figures)
    - Capitalized words (named entities)

    Args:
        text: Input text to sample
        max_words: Maximum words to return

    Returns:
        String containing most important sentences up to max_words
    """
    # Keywords for importance scoring
    financial_kw = ['revenue', 'earnings', 'profit', 'loss', 'quarter', 'year',
                    'growth', 'margin', 'ebitda', 'cash', 'debt', 'sales', 'income']
    entity_kw = ['inc', 'corp', 'company', 'ltd', 'llc', 'corporation']
    action_kw = ['announced', 'reported', 'filed', 'disclosed', 'stated',
                 'released', 'published', 'showed', 'increased', 'decreased']

    all_keywords = financial_kw + entity_kw + action_kw

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Score each sentence
    scored_sentences = []
    for sent in sentences:
        if not sent.strip():
            continue

        sent_lower = sent.lower()
        score = 0.0

        # Keyword matching (main scoring factor)
        for kw in all_keywords:
            score += sent_lower.count(kw)

        # Bonus for numbers (likely financial data)
        score += len(re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?%?\b', sent)) * 0.5

        # Bonus for capitalized words (named entities, companies, people)
        score += len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sent)) * 0.3

        scored_sentences.append((score, sent))

    # Sort by score descending (highest importance first)
    scored_sentences.sort(reverse=True, key=lambda x: x[0])

    # Select top sentences up to max_words
    selected = []
    current_words = 0

    for score, sent in scored_sentences:
        sent_word_count = len(sent.split())
        if current_words + sent_word_count <= max_words:
            selected.append(sent)
            current_words += sent_word_count

        if current_words >= max_words:
            break

    return " ".join(selected)


def clean_text(text: str, max_words: int = 5000) -> str:
    """
    Clean and preprocess text for classification using dynamic sampling strategy.

    Strategy selection based on document length:
    - ≤ 5,000 words (57.5% of docs): No sampling, use full text
    - 5,001 - 20,000 words (25.9% of docs): Weighted beginning-heavy sampling (70/20/10)
    - > 20,000 words (16.6% of docs): Importance-based sentence scoring

    Args:
        text: Input text to clean
        max_words: Maximum number of words to process (default 5000 for performance)

    Returns:
        Cleaned and preprocessed text ready for classification
    """
    words = text.split()
    word_count = len(words)

    # Strategy selection based on document length
    if word_count <= max_words:
        # No sampling needed for short/medium documents
        sampled_text = text
        strategy = "none"

    elif word_count <= 20000:
        # Strategy 1: Weighted beginning-heavy sampling for long documents
        # 70% from beginning, 20% from middle, 10% from end
        beginning_size = int(max_words * 0.7)  # 3,500 words
        middle_size = int(max_words * 0.2)     # 1,000 words
        end_size = max_words - beginning_size - middle_size  # 500 words

        beginning = words[:beginning_size]
        middle_start = word_count // 2 - middle_size // 2
        middle = words[middle_start:middle_start + middle_size]
        end = words[-end_size:]

        sampled_text = " ".join(beginning + middle + end)
        strategy = "weighted"

    else:
        # Strategy 2: Importance-based sampling for very long documents
        # Uses keyword density and sentence scoring
        sampled_text = _importance_sample(text, max_words)
        strategy = "importance"

    # Log sampling strategy used (useful for monitoring)
    print(f"[clean_text] Document: {word_count:,} words → Strategy: {strategy} → Sampled: {len(sampled_text.split()):,} words")

    # Apply text cleaning to sampled text
    sampled_text = sampled_text.lower()
    sampled_text = re.sub(r"[^a-z\s]", " ", sampled_text)
    tokens = [tok for tok in sampled_text.split() if tok not in ENGLISH_STOP_WORDS]

    return " ".join(tokens)
