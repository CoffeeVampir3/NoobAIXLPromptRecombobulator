import polars as pl
from typing import List, Optional, Set
import csv
from io import StringIO

SYNTHETIC_CATEGORY_TAGS = {
    # Count tags
    "1girl", "2girls", "3girls", "4girls", "5girls", "6girls", "7girls", "8girls", "9girls",
    "1other", "2others", "3others", "4others", "5others", "6others", "7others", "8others", "9others",
    "1boy", "2boys", "3boys", "4boys", "5boys", "6boys", "7boys", "8boys", "9boys",
    # Quality and resolution tags
    "masterpiece", "best quality", "good quality", "normal quality", "worst quality",
    "absurdres", "highres", "mediumres", "lowres", "old", "early", "mid", "recent", "newest",
    "very awa", "worst aesthetic",
    # Additional resolution-related tags
    "ultrahighres", "superres", "extremeres", "megares", "gigares",
    "ultrares", "superhighres", "extremehighres", "megahighres", "gigahighres"
}

def load_tag_dataset(filepath: str) -> pl.DataFrame:
    """
    Load a tag dataset with aliases into a Polars DataFrame.
    
    The input file should have the format:
    id,category,post_count,aliases
    
    Where aliases can be:
    - Empty (no aliases)
    - Single value
    - Comma-separated list in quotes
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        pl.DataFrame: DataFrame with columns [id, category, post_count, aliases]
        where aliases is a list column
    """
    
    def parse_aliases(aliases: str) -> Optional[List[str]]:
        """Parse the aliases field into a list of strings."""
        if not aliases or aliases.isspace():
            return None
        
        # Remove any surrounding quotes
        aliases = aliases.strip('"\'')
        
        # Split on comma and clean each alias
        return [alias.strip() for alias in aliases.split(',') if alias.strip()]
    
    # Read the raw CSV content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a CSV reader that handles quoted fields
    reader = csv.reader(StringIO(content))
    
    # Skip header
    next(reader)
    
    # Parse rows
    rows = []
    for row in reader:
        if len(row) >= 4:  # Ensure we have all required fields
            id_val, category, post_count, *alias_fields = row
            
            # Join any remaining fields in case the aliases contained commas
            aliases_str = ','.join(alias_fields).strip()
            
            # Parse the aliases
            aliases_list = parse_aliases(aliases_str)
            
            rows.append({
                'id': id_val,
                'category': int(category),
                'post_count': int(post_count),
                'aliases': aliases_list
            })
    
    # Create DataFrame
    df = pl.DataFrame(rows)
    
    return df

def inject_or_change_specials(df: pl.DataFrame, special_tags: Set[str] = None) -> pl.DataFrame:
    """
    Inject or update special tags in the dataset with category 9.
    Special tags maintain their original format (with spaces).
    """
    if special_tags is None:
        special_tags = SYNTHETIC_CATEGORY_TAGS
    
    # Create a case-insensitive lookup for existing tags
    existing_tags_lower = {tag.lower(): tag for tag in df['id'].to_list()}
    
    # Prepare new rows for injection
    new_rows = []
    
    for tag in special_tags:
        tag_lower = tag.lower()
        
        if tag_lower in existing_tags_lower:
            # Get the exact tag from the database
            db_tag = existing_tags_lower[tag_lower]
            # Update existing tag's category to 9
            df = df.with_columns(
                pl.when(pl.col('id').str.to_lowercase() == tag_lower)
                .then(pl.lit(9))
                .otherwise(pl.col('category'))
                .alias('category')
            )
            
            # Debug print to verify the update
            print(f"Updating existing tag '{db_tag}' to category 9")
        else:
            # Create new row for non-existing tag, maintaining original format
            new_rows.append({
                'id': tag,
                'category': 9,
                'post_count': 0,
                'aliases': None
            })
            print(f"Adding new synthetic tag '{tag}'")
    
    # If we have new rows, append them to the DataFrame
    if new_rows:
        new_df = pl.DataFrame(new_rows)
        df = pl.concat([df, new_df], how='vertical')
        
    # Debug: verify the results
    synthetic_tags_in_db = df.filter(pl.col('category') == 9)['id'].to_list()
    print(f"\nSynthetic tags in database after injection:")
    print(synthetic_tags_in_db)
    
    return df