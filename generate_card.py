import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from word import get_random_word_from_level
from explain_word import explain_word, load_env_vars
from generate_audio import generate_audio
from generate_image import generate_image, extract_definition

def parse_explanation(explanation):
    """Parses the explanation to extract sections."""
    sections = {}
    
    patterns = {
        "Phonetic Transcription": r"Phonetic Transcription:\s*(.*?)(?=Definition\(s\):|$)",
        "Definition": r"Definition\(s\):\s*(.*?)(?=Synonyms:|$)",
        "Synonyms": r"Synonyms:\s*(.*?)(?=Antonyms \(if applicable\):|Example Sentences:|$)",
        "Antonyms": r"Antonyms \(if applicable\):\s*(.*?)(?=Example Sentences:|$)",
        "Example Sentences": r"Example Sentences:\s*(.*?)(?=Writing|$)",
        "Writing": r"Writing.*:\s*(.*)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, explanation, re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
        else:
            sections[key] = ""
            
    return sections

def clean_text(text):
    """Removes numbering and converts Markdown to HTML."""
    if not text:
        return ""
    
    # Remove leading numbers like "1. ", "2. "
    cleaned = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Convert Markdown bold (**text**) to HTML (<b>text</b>)
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned)
    
    # Convert Markdown italic (*text*) to HTML (<i>text</i>)
    cleaned = re.sub(r'\*(.*?)\*', r'<i>\1</i>', cleaned)
    
    # Replace newlines with <br>
    cleaned = cleaned.replace('\n', '<br>')
    
    return cleaned

def create_section_html(title, content, audio_button=""):
    """Creates a styled HTML section."""
    return f"""
    <div style="margin-bottom: 30px;">
        <h3 style="
            color: #d35400;
            border-bottom: 2px solid #fcebe1;
            padding-bottom: 8px;
            margin-bottom: 12px;
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        ">
            {title} {audio_button}
        </h3>
        <div style="color: #4a5568;">
            {content}
        </div>
    </div>
    """

def create_card(word, explanation, sections, image_filename, word_audio_filename, explanation_audio_filename):
    """Populates the template with data."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "card_template.md")
    
    try:
        with open(template_path, 'r') as f:
            template = f.read()
    except FileNotFoundError:
        print("Error: card_template.md not found.")
        return

    # 1. Image
    template = template.replace('IMAGE_PLACEHOLDER', image_filename)
    
    # 2. Word + Audio Button
    word_capitalized = word.capitalize()
    audio_button_md = f'<a href="{word_audio_filename}" style="text-decoration:none; font-size: 0.5em; vertical-align: middle; margin-left: 15px; opacity: 0.7;">🔊</a>'
    template = template.replace('WORD_PLACEHOLDER', f'{word_capitalized}{audio_button_md}')
    
    # 3. Phonetic Transcription Badge
    phonetic = sections.get("Phonetic Transcription", "")
    pos_html = ""
    if phonetic:
        pos_html = f"""
        <span style="
            background-color: #edf2f7;
            color: #718096;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
            display: inline-block;
        ">{phonetic}</span>
        """
    template = template.replace('POS_PLACEHOLDER', pos_html)
    
    # 4. Construct Body Content
    body_content = ""
    
    # Definition
    definition = sections.get("Definition")
    if definition:
        body_content += create_section_html("Definition", clean_text(definition))
    
    # Synonyms
    synonyms = sections.get("Synonyms")
    if synonyms:
        body_content += create_section_html("Synonyms", clean_text(synonyms))
        
    # Antonyms
    antonyms = sections.get("Antonyms")
    if antonyms and "None" not in antonyms:
        body_content += create_section_html("Antonyms", clean_text(antonyms))
        
    # Example Sentences
    sentences = sections.get("Example Sentences")
    if sentences:
        body_content += create_section_html("Example Sentences", clean_text(sentences))
        
    # Writing
    writing = sections.get("Writing")
    if writing:
        explanation_audio_button = f'<a href="{explanation_audio_filename}" style="text-decoration:none; font-size: 0.8em; vertical-align: middle; margin-left: 8px; opacity: 0.8;">🔊</a>'
        body_content += create_section_html("Writing", clean_text(writing), explanation_audio_button)
        
    template = template.replace('BODY_PLACEHOLDER', body_content)

    output_path = os.path.join(script_dir, "word_card.md")
    with open(output_path, 'w') as f:
        f.write(template)
    print(f"Card saved to {output_path}")

def generate_card_data(target_word=None, voice_id='Joanna', level='junior', text_model='mistral', audio_model='polly'):
    """Orchestrates generation and returns data dictionary.

    Args:
        target_word: Word to generate card for (None for random)
        voice_id: Voice ID for TTS
        level: Vocabulary level (default: junior)
        text_model: Text generation model - 'mistral' or 'deepseek' (default: mistral)
        audio_model: Audio generation model - 'polly' or 'deepgram' (default: polly)
    """
    load_env_vars()

    # Validate API keys are available
    # Validate API keys based on selected model
    missing_keys = []
    
    # Check text model keys
    if text_model == 'mistral' and not os.environ.get("MISTRAL_API_KEY"):
        missing_keys.append("MISTRAL_API_KEY")
    elif text_model == 'gemini':
        # Gemini supports both Vertex AI (project_id) and API Key modes
        project_id = os.environ.get("GOOGLE_PROJECT_ID")
        api_key = os.environ.get("GOOGLE_API_KEY")
        has_vertexai = project_id and project_id != "YOUR_PROJECT_ID"
        if not api_key and not has_vertexai:
            missing_keys.append("GOOGLE_API_KEY or GOOGLE_PROJECT_ID")
    elif text_model == 'deepseek' and not os.environ.get("DEEPSEEK_API_KEY"):
        missing_keys.append("DEEPSEEK_API_KEY")
        
    # Check audio model keys (if applicable)
    if audio_model == 'deepgram' and not os.environ.get("DEEPGRAM_API_KEY"):
        missing_keys.append("DEEPGRAM_API_KEY")
    # AWS credentials for Polly are handled by boto3

    if missing_keys:
        return {"error": f"Missing API keys for selected models: {', '.join(missing_keys)}. Please check your .env file."}

    data = {}

    # 1. Get Word
    if target_word:
        word = target_word
        print(f"Using provided word: {word}")
    else:
        print(f"Fetching random word from level: {level}...")
        word = get_random_word_from_level(level)
        print(f"Word: {word}")

    if "Error" in word or "No words" in word:
        return {"error": word}

    data["word"] = word

    # 2. Explanation (using selected text model)
    print(f"Generating explanation with {text_model}...")
    explanation = explain_word(word, text_model=text_model)
    if explanation.startswith("Error") or explanation.startswith("HTTP Error") or explanation.startswith("Connection Error"):
        return {"error": f"Failed to generate explanation: {explanation}"}

    # 3. Parse
    print("RAW EXPLANATION FROM AI:")
    print(explanation)
    print("------------------------")
    sections = parse_explanation(explanation)
    data["sections"] = sections

    # 4. Generate Image & Audio in parallel for better performance
    definition = sections.get("Definition")
    if not definition:
        definition = word

    print(f"Generating image and audio in parallel (audio model: {audio_model})...")
    # Use UUID for unique audio filenames only (image uses word-based naming)
    session_id = str(uuid.uuid4())

    # Ensure static directory exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(script_dir, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Import helper function for consistent naming
    from generate_image import sanitize_filename

    # Image: use word-based filename in public/generate_picture/
    safe_word = sanitize_filename(word)
    image_filename = f"{safe_word}.png"
    image_url_path = f"/public/generate_picture/{image_filename}"

    # Audio: use session-based filenames in static/
    word_audio_filename = f"word_audio_{session_id}.mp3"
    explanation_audio_filename = f"explanation_audio_{session_id}.mp3"

    # No need to specify image_path, generate_image will use cache path
    word_audio_path = os.path.join(static_dir, word_audio_filename)
    explanation_audio_path = os.path.join(static_dir, explanation_audio_filename)

    writing_text = sections.get("Writing", "")
    explanation_text = writing_text if writing_text else explanation

    # Parallel execution using ThreadPoolExecutor
    # Increased workers from 3 to 6 for better performance
    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all tasks
        # For image: pass None as filename, word parameter will determine cache path
        future_image = executor.submit(generate_image, definition, None, word)
        future_word_audio = executor.submit(generate_audio, word, word_audio_path, voice_id, audio_model)
        future_explanation_audio = executor.submit(generate_audio, explanation_text, explanation_audio_path, voice_id, audio_model)

        # Collect results
        results = {}
        for future in as_completed([future_image, future_word_audio, future_explanation_audio]):
            try:
                result = future.result()
                if future == future_image:
                    results['image'] = result
                    if result:
                        print("✓ Image generated")
                elif future == future_word_audio:
                    results['word_audio'] = result
                    if result:
                        print("✓ Word audio generated")
                elif future == future_explanation_audio:
                    results['explanation_audio'] = result
                    if result:
                        print("✓ Explanation audio generated")
            except Exception as e:
                print(f"Error in parallel task: {e}")
                if future == future_image:
                    results['image'] = False
                elif future == future_word_audio:
                    results['word_audio'] = False
                elif future == future_explanation_audio:
                    results['explanation_audio'] = False

    # Check results and return errors if needed
    if not results.get('image'):
        return {"error": "Failed to generate image"}

    if not results.get('word_audio'):
        return {"error": "Failed to generate word audio"}

    if not results.get('explanation_audio'):
        return {"error": "Failed to generate explanation audio"}

    # All successful
    data["image_url"] = image_url_path  # Already set to /public/generate_picture/{word}.png
    data["word_audio_url"] = f"/static/{word_audio_filename}"
    data["explanation_audio_url"] = f"/static/{explanation_audio_filename}"

    print("All assets generated successfully!")
    return data

if __name__ == "__main__":
    # Legacy support for running directly
    data = generate_card_data()
    if "error" in data:
        print(data["error"])
    else:
        # Create the markdown card for backward compatibility
        create_card(
            data["word"], 
            "", # Raw explanation not needed for create_card anymore as we pass sections
            data["sections"], 
            "static/word_image.png", # Relative path for the markdown file if it's in root
            "static/word_audio.mp3", 
            "static/explanation_audio.mp3"
        )
        print("Done!")
