import polars as pl
from typing import List, Tuple, Dict, Set

def rearrange_prompt(df: pl.DataFrame, input_text: str, tags: Set[str],
                    alias_map: Dict[str, str], notate_artists: bool = True) -> str:
    """
    Rearranges input text based on tag categories in the priority order: 9, 4, 1, 0, 5, others
    """
    if not input_text:
        return ""

    # Split input on commas and clean up whitespace
    words = [word.strip() for word in input_text.split(',')]
    words = [word for word in words if word]

    # Create category lookup from DataFrame
    category_lookup = {}
    for row in df.iter_rows(named=True):
        tag_id = row['id'].lower()
        category = row['category']
        category_lookup[tag_id] = category

    word_categories = []
    for i, word in enumerate(words):
        word_lower = word.lower()
        cleaned_word = word_lower.replace('\\(', '(').replace('\\)', ')')
        # Try both with and without underscore
        category = category_lookup.get(cleaned_word, -1)
        if category == -1:
            cleaned_word_underscore = cleaned_word.replace(' ', '_')
            category = category_lookup.get(cleaned_word_underscore, -1)

        word_categories.append((word, category, i))

    # Group by category
    category_groups = {9: [], 4: [], 1: [], 0: [], 5 : [], -1: []}
    for word, category, original_pos in word_categories:
        actual_category = category if category in [9, 4, 1, 0, 5] else -1
        category_groups[actual_category].append((word, original_pos))

    # Build result
    result_parts = []
    priority_order = [9, 4, 1, 0, 5, -1]
    
    for cat in priority_order:
        if category_groups[cat]:
            sorted_words = sorted(category_groups[cat], key=lambda x: x[1])
            words_in_category = [word for word, _ in sorted_words]
            
            if cat == 1 and notate_artists:
                words_in_category = [f"artist:{word}" for word in words_in_category]
            
            if result_parts:
                result_parts.append(", ")
            result_parts.append(", ".join(words_in_category))

    result = "".join(result_parts)
    return result