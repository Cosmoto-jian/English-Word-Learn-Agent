import os
import json
import urllib.request
import urllib.error
import re
import base64
from word import get_random_word
from explain_word import explain_word, load_env_vars

# Google Gemini support
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai package not installed. Please install it with: pip install google-genai")

def sanitize_filename(word):
    """Sanitize word to create a safe filename."""
    # Remove or replace unsafe characters
    safe_word = re.sub(r'[<>:"/\\|?*\']', '', word)
    safe_word = safe_word.strip().lower()
    return safe_word if safe_word else 'unknown'

def get_cache_path(word):
    """Get the cache file path for a word.

    Args:
        word: The word to get cache path for

    Returns:
        str: Full path to the cache file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(script_dir, "public", "generate_picture")

    # Create directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"Created cache directory: {cache_dir}")

    safe_word = sanitize_filename(word)
    return os.path.join(cache_dir, f"{safe_word}.png")

def extract_definition(explanation):
    """Extracts the primary definition from the explanation text."""
    try:
        # Look for "Definition(s):" followed by "1. [text]"
        match = re.search(r"Definition\(s\):\s*\n1\.\s*(.+)", explanation)
        if match:
            return match.group(1).strip()
        
        # Fallback: try to find just "1. " if the header is slightly different
        match = re.search(r"\n1\.\s*(.+)", explanation)
        if match:
            return match.group(1).strip()
            
        return None
    except Exception as e:
        print(f"Error extracting definition: {e}")
        return None

def generate_image_siliconflow(prompt, filepath):
    """Generate image using SiliconFlow Qwen-Image API.

    Args:
        prompt: Text prompt for image generation
        filepath: Target file path to save the image

    Returns:
        bool: True if successful, False otherwise
    """
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        print("Error: SILICONFLOW_API_KEY not found in environment variables.")
        return False

    url = "https://api.siliconflow.cn/v1/images/generations"

    # System prompt for anime style image generation
    system_prompt = """Anime illustration master style: Create a single, visually striking image that perfectly embodies and explains the exact meaning of the English word or phrase.
Depict the concept through expressive anime characters (girls/boys with detailed eyes and hair), dynamic poses, facial expressions, body language, interactions, or short dialogue bubbles.
Use symbolic scenes, metaphors, or literal scenarios typical in anime to make the meaning instantly clear and emotionally resonant.
Highly detailed, vibrant colors, cinematic lighting, masterpiece quality, best anime art style (1990s–2020s blend), 4k, perfect composition.
Never write the word itself as overlay text unless it naturally appears as dialogue."""

    # Combine system prompt with user input
    full_prompt = f"{system_prompt}\n\nConcept to illustrate: {prompt}"

    payload = {
        "model": "Qwen/Qwen-Image",
        "prompt": full_prompt,
        "batch_size": 1,
        "num_inference_steps": 50,
        "guidance_scale": 4.0,
        "image_size": "1664x928"  # 16:9 aspect ratio
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        print(f"[SiliconFlow] Generating image for prompt: '{prompt}'...")
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )

        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Check if images were generated
            if 'images' not in result or not result['images']:
                print("[SiliconFlow] Error: No images in response")
                return False

            # Get the first image
            image_data = result['images'][0]

            # Check if it's a URL or base64 data
            if 'url' in image_data:
                # Download from URL
                image_url = image_data['url']
                print(f"[SiliconFlow] Downloading image from URL...")

                img_req = urllib.request.Request(image_url)
                with urllib.request.urlopen(img_req, timeout=30) as img_response:
                    img_bytes = img_response.read()
                    with open(filepath, 'wb') as f:
                        f.write(img_bytes)
            elif 'b64_json' in image_data:
                # Decode base64 data
                print(f"[SiliconFlow] Decoding base64 image data...")
                img_bytes = base64.b64decode(image_data['b64_json'])
                with open(filepath, 'wb') as f:
                    f.write(img_bytes)
            else:
                print("[SiliconFlow] Error: No image URL or base64 data in response")
                return False

            print(f"[SiliconFlow] ✓ Image saved to {filepath}")
            return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        print(f"[SiliconFlow] HTTP Error: {e.code} {e.reason}")
        print(f"[SiliconFlow] Error details: {error_body}")
        return False
    except urllib.error.URLError as e:
        print(f"[SiliconFlow] Connection Error: {e.reason}")
        return False
    except Exception as e:
        print(f"[SiliconFlow] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_image(prompt, filename, word=None):
    """Generate image from prompt using Google Gemini as primary provider with SiliconFlow fallback.

    Uses Google Gemini Imagen API as primary, with SiliconFlow Qwen-Image as fallback.

    Args:
        prompt: Text prompt for image generation
        filename: Target filename for the generated image (used if word is None)
        word: Optional word name for caching (if provided, uses cache path directly)

    Returns:
        bool: True if successful, False otherwise
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine the target filepath
    if word:
        # Use cache path directly (no copying needed)
        filepath = get_cache_path(word)

        # Check if already cached
        if os.path.exists(filepath):
            print(f"✓ Using cached image: {filepath}")
            return True

        print(f"Cache miss for '{word}', generating new image...")
    else:
        # Fallback: use provided filename
        filepath = os.path.join(script_dir, filename)

    # Use Google Gemini as primary provider
    api_key = os.environ.get("GOOGLE_API_KEY")
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    gemini_available = GENAI_AVAILABLE and (api_key or (project_id and project_id != "YOUR_PROJECT_ID"))

    if gemini_available:
        print("[Image Generation] Using Google Gemini Imagen...")
        success = _generate_image_gemini(prompt, filepath)
        if success:
            return True
        print("[Image Generation] Gemini generation failed")

    # # SiliconFlow fallback (commented out - Gemini is primary)
    # print("[Image Generation] Trying SiliconFlow Qwen-Image as fallback...")
    # success = generate_image_siliconflow(prompt, filepath)
    # if success:
    #     return True
    # print("[Image Generation] SiliconFlow also failed")

    return False

def _generate_image_gemini(prompt, filepath):
    """Generate image using Google Gemini Image Generation API (Vertex AI or API Key mode).

    Args:
        prompt: Text prompt for image generation
        filepath: Target file path to save the image

    Returns:
        bool: True if successful, False otherwise
    """
    if not GENAI_AVAILABLE:
        print("[Gemini] Error: google-genai package not installed.")
        return False

    # Check for Vertex AI configuration
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    location = os.environ.get("GOOGLE_LOCATION", "global")
    api_key = os.environ.get("GOOGLE_API_KEY")

    # Determine which mode to use
    use_vertexai = project_id and project_id != "YOUR_PROJECT_ID"

    # System prompt for anime style image generation
    system_prompt = """Anime illustration master style: Create a single, visually striking image that perfectly embodies and explains the exact meaning of the English word or phrase.
Depict the concept through expressive anime characters (girls/boys with detailed eyes and hair), dynamic poses, facial expressions, body language, interactions, or short dialogue bubbles.
Use symbolic scenes, metaphors, or literal scenarios typical in anime to make the meaning instantly clear and emotionally resonant.
Highly detailed, vibrant colors, cinematic lighting, masterpiece quality, best anime art style (1990s–2020s blend), 4k, perfect composition.
Never write the word itself as overlay text unless it naturally appears as dialogue.
Generate the image with 16:9 aspect ratio (1664x928 pixels)."""

    # Combine system prompt with user input
    full_prompt = f"{system_prompt}\n\nConcept to illustrate: {prompt}"

    try:
        if use_vertexai:
            # Vertex AI mode
            print(f"[Gemini] Using Vertex AI mode (Project: {project_id}, Location: {location})")
            client = genai.Client(vertexai=True, project=project_id, location=location)
            model = "gemini-2.5-flash-image-preview"
        else:
            # API Key mode - use Imagen API
            if not api_key:
                print("[Gemini] Error: GOOGLE_API_KEY not found in environment variables.")
                return False

            print(f"[Gemini] Using API Key mode")
            client = genai.Client(api_key=api_key)
            # API Key mode uses imagen model
            model = "imagen-4.0-generate-001"

            # For API Key mode, use the old generate_images API
            print(f"[Gemini] Generating image for prompt: '{prompt}'...")
            response = client.models.generate_images(
                model=model,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio='16:9',
                    safety_filter_level='block_low_and_above',
                    person_generation='allow_adult'
                )
            )

            # Check if image was generated
            if not response.generated_images or len(response.generated_images) == 0:
                print("[Gemini] Error: No images generated")
                return False

            # Get the first generated image
            generated_image = response.generated_images[0]

            # Save the image
            if hasattr(generated_image.image, '_pil_image'):
                pil_image = generated_image.image._pil_image
                pil_image.save(filepath, format='PNG')
            else:
                # Fallback: save using the image bytes
                image_bytes = generated_image.image._image_bytes
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

            print(f"[Gemini] ✓ Image saved to {filepath}")
            return True

        # Vertex AI mode - use generate_content with image response
        print(f"[Gemini] Generating image with model: {model}")
        print(f"[Gemini] Prompt: '{prompt}'")

        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                candidate_count=1,
            ),
        )

        # Extract image from response
        image_saved = False
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Save the inline image data
                with open(filepath, 'wb') as f:
                    f.write(part.inline_data.data)
                print(f"[Gemini] ✓ Image saved to {filepath}")
                image_saved = True
                break

        if not image_saved:
            print("[Gemini] Error: No image data in response")
            # Print text response if available for debugging
            for part in response.candidates[0].content.parts:
                if part.text:
                    print(f"[Gemini] Text response: {part.text}")
            return False

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini] Error: {error_msg}")

        # Check if it's a geographic restriction error
        if 'location is not supported' in error_msg.lower() or 'FAILED_PRECONDITION' in error_msg:
            print("[Gemini] Geographic restriction detected - API not available in your region")

        # Don't print full traceback for known errors
        if 'FAILED_PRECONDITION' not in error_msg:
            import traceback
            traceback.print_exc()

        return False

if __name__ == "__main__":
    # Load environment variables
    load_env_vars()
    
    # 1. Get random word
    print("Fetching random word...")
    word = get_random_word()
    print(f"Selected word: {word}")
    
    if "Error" in word or "No words" in word:
        print("Aborting due to word fetch error.")
    else:
        # 2. Get explanation
        print("\nGenerating explanation...")
        explanation = explain_word(word)
        
        if explanation and not explanation.startswith("Error"):
            # 3. Extract definition
            definition = extract_definition(explanation)
            
            if definition:
                print(f"\nExtracted Definition: {definition}")
                # 4. Generate image
                generate_image(definition, "word_image.png")
            else:
                print("Could not extract definition from explanation.")
                print("Full explanation:\n", explanation)
        else:
            print(f"Failed to generate explanation: {explanation}")
