import gradio as gr
import polars as pl
from typing import List, Tuple, Optional, Dict, Set
from modules.tag_loader import load_tag_dataset, inject_or_change_specials, SYNTHETIC_CATEGORY_TAGS
from modules.prompt_rearranger import rearrange_prompt

def build_tag_maps(df: pl.DataFrame) -> Tuple[Set[str], Dict[str, str]]:
    """
    Build maps for tags and their aliases.
    Returns:
        Tuple of (set of tags, dict of alias->tag mappings)
    """
    # Convert tags to lowercase for case-insensitive matching
    tags = set(tag.lower() for tag in df['id'].to_list())
    
    # Build alias map
    alias_map = {}
    for row in df.iter_rows(named=True):
        tag = row['id'].lower()
        if row['aliases']:
            for alias in row['aliases']:
                alias_map[alias.lower()] = tag
    
    return tags, alias_map

def clean_tag_for_matching(tag: str) -> str:
    tag = tag.lower()
    # Replace spaces with underscores
    tag = tag.replace(' ', '_')
    return tag

def highlight_text(text: str, tags: Set[str], alias_map: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Highlight text based on whether words are tags, aliases, or neither.
    Special handling for synthetic tags to preserve spaces.
    Preserves 'artist:' prefix in output but ignores it for matching.
    """
    if not text:
        return []

    text = text.replace('\\(', '(').replace('\\)', ')')
    text = text.replace('artist:', '')
    text = rearrange_prompt(df, text, tags, alias_map)
    
    # Split on commas and clean up whitespace
    terms = [term.strip() for term in text.split(',')]
    terms = [term for term in terms if term]  # Remove empty strings
    
    result = []
    
    for i, term in enumerate(terms):
        original_term = term
        
        # Check for artist: prefix
        has_prefix = term.lower().startswith('artist:')
        if has_prefix:
            term_to_check = term[7:]  # Remove 'artist:' prefix for matching
        else:
            term_to_check = term
            
        term_lower = term_to_check.lower()
        
        # First check if it's a synthetic tag (exact match with spaces)
        if term_lower in {t.lower() for t in SYNTHETIC_CATEGORY_TAGS}:
            result.append((original_term, "tag"))  # Keep original format with prefix if present
        else:
            # Handle regular tags (with underscore conversion)
            cleaned_term = clean_tag_for_matching(term_to_check)
            
            if cleaned_term in tags:
                result.append((original_term, "tag"))  # Keep original format with prefix if present
            elif cleaned_term in alias_map:
                main_tag = alias_map[cleaned_term]
                result.append((original_term, "alias"))  # Keep original format with prefix if present
            else:
                result.append((original_term, "unknown"))
        
        # Add comma and space between terms (except for last term)
        if i < len(terms) - 1:
            result.append((", ", None))
    
    return result

# Load the database
df = load_tag_dataset("./danbooru-12-10-24-underscore.csv")
df = inject_or_change_specials(df)

tags, alias_map = build_tag_maps(df)

# Create the interface
with gr.Blocks() as demo:
    gr.Markdown("""
    # Tag Highlighter
    
    Enter text to highlight Danbooru tags:
    - **Green**: Direct tag match
    - **Orange**: Alias match
    - **Black**: Not found
    
    Tags will be automatically rearranged by category in the order: 4, 1, 0, others
    """)
    
    text_input = gr.Textbox(
        label="Enter text",
        placeholder="Type something with tags...",
        info="Enter text to check for tags",
        lines=3,
        show_copy_button=True
    )
    
    highlighted_output = gr.HighlightedText(
        label="Highlighted Tags",
        show_legend=True,
        color_map={
            "tag": "green",
            "alias": "orange",
            "unknown": "gray"
        }
    )
    
    def process_text(text: str) -> List[Tuple[str, str]]:
        return highlight_text(text, tags, alias_map)
    
    # Update output whenever input changes
    text_input.change(
        fn=process_text,
        inputs=[text_input],
        outputs=[highlighted_output]
    )
    
    # Also add a button for manual update
    highlight_btn = gr.Button("Highlight Text")
    highlight_btn.click(
        fn=process_text,
        inputs=[text_input],
        outputs=[highlighted_output]
    )

if __name__ == "__main__":
    demo.launch()