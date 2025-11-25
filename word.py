import json
import random
import os
import re

# Level configuration mapping
LEVEL_CONFIG = {
    "junior": {
        "name": "初中",
        "file": "1 初中-乱序_3223.sql",
        "count": 3223
    },
    "senior": {
        "name": "高中",
        "file": "2 高中-乱序_6008.sql",
        "count": 6008
    },
    "cet4": {
        "name": "四级",
        "file": "3 四级-乱序_7508.sql",
        "count": 7508
    },
    "cet6": {
        "name": "六级",
        "file": "4 六级-乱序_5661.sql",
        "count": 5661
    },
    "toefl": {
        "name": "托福",
        "file": "6 托福-乱序_13477.sql",
        "count": 13477
    },
    "sat": {
        "name": "SAT",
        "file": "7 SAT-乱序_8887.sql",
        "count": 8887
    }
}

def get_available_levels():
    """Get list of available vocabulary levels"""
    return [
        {"id": key, "name": config["name"], "count": config["count"]}
        for key, config in LEVEL_CONFIG.items()
    ]

def parse_sql_words(sql_content):
    """Parse SQL file and extract words

    Args:
        sql_content: SQL file content as string

    Returns:
        list: List of words extracted from INSERT statements
    """
    words = []
    # Regex pattern to match: INSERT INTO table (word,translate) VALUES ('word','translation');
    pattern = r"INSERT INTO \w+ \(word,translate\) VALUES \('([^']+)','[^']*'\);"

    matches = re.findall(pattern, sql_content)
    words.extend(matches)

    return words

def get_random_word_from_level(level="junior"):
    """Get a random word from specified level's SQL file

    Args:
        level: Vocabulary level (junior, senior, cet4, cet6, toefl, sat)

    Returns:
        str: Random word from the level, or error message
    """
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Validate level
    if level not in LEVEL_CONFIG:
        return f"Error: Invalid level '{level}'. Valid levels: {', '.join(LEVEL_CONFIG.keys())}"

    # Construct SQL file path
    sql_file = LEVEL_CONFIG[level]["file"]
    sql_path = os.path.join(script_dir, "public", "dicts", "word", sql_file)

    try:
        # Read and parse SQL file
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Extract words from SQL
        words = parse_sql_words(sql_content)

        if not words:
            return f"Error: No words found in {sql_file}"

        # Return random word
        random_word = random.choice(words)
        return random_word

    except FileNotFoundError:
        return f"Error: SQL file not found at {sql_path}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_random_word():
    """Legacy function for backward compatibility - uses junior level by default"""
    return get_random_word_from_level("junior")

if __name__ == "__main__":
    print("Testing vocabulary levels:")
    print("=" * 50)

    # Test all levels
    for level_id in LEVEL_CONFIG.keys():
        word = get_random_word_from_level(level_id)
        level_name = LEVEL_CONFIG[level_id]["name"]
        print(f"{level_name} ({level_id}): {word}")

    print("\n" + "=" * 50)
    print("Available levels:")
    for level in get_available_levels():
        print(f"  - {level['name']} ({level['id']}): {level['count']} words")