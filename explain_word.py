import os
import json
import urllib.request
import urllib.error
from word import get_random_word

def load_env_vars():
    """Simple .env loader to avoid external dependencies."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Only process lines with '='
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove surrounding quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value
        print(f"Loaded environment variables from {env_path}")
    except FileNotFoundError:
        print(f"Warning: {env_path} not found.")
    except Exception as e:
        print(f"Error loading .env file: {e}")

# =============================================================================
# Unified Response Handlers (used by both models)
# =============================================================================

def _sync_response(url, payload, headers):
    """Synchronous (non-streaming) version - unified for all models."""
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Validate response structure
            if not isinstance(result, dict):
                return "Error: Invalid API response format"
            if 'choices' not in result or not result['choices']:
                return "Error: No choices in API response"
            if 'message' not in result['choices'][0]:
                return "Error: No message in API response"
            if 'content' not in result['choices'][0]['message']:
                return "Error: No content in API response"

            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        return f"HTTP Error: {e.code} {e.reason}\n{error_body}"
    except urllib.error.URLError as e:
        return f"Connection Error: {e.reason}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response from API"
    except Exception as e:
        return f"Error: {str(e)}"

def _stream_response(url, payload, headers):
    """Streaming version - yields text chunks as they arrive (unified for all models)."""
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)

        with urllib.request.urlopen(req, timeout=60) as response:
            accumulated_text = ""

            for line in response:
                line = line.decode('utf-8').strip()

                # Skip empty lines and comments
                if not line or line.startswith(':'):
                    continue

                # Remove "data: " prefix
                if line.startswith('data: '):
                    line = line[6:]

                # Check for end of stream
                if line == '[DONE]':
                    break

                try:
                    chunk_data = json.loads(line)

                    # Extract content from the chunk
                    if 'choices' in chunk_data and chunk_data['choices']:
                        delta = chunk_data['choices'][0].get('delta', {})
                        content = delta.get('content', '')

                        if content:
                            accumulated_text += content
                            yield content

                except json.JSONDecodeError:
                    continue

            # Return full text if nothing was streamed
            if not accumulated_text:
                raise Exception("No content received from streaming API")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        yield f"HTTP Error: {e.code} {e.reason}\n{error_body}"
    except urllib.error.URLError as e:
        yield f"Connection Error: {e.reason}"
    except Exception as e:
        yield f"Error: {str(e)}"

# =============================================================================
# Word Explanation Functions
# =============================================================================

def explain_word(word, stream=False, text_model='mistral'):
    """Generate explanation for a word using specified text model.

    Args:
        word: The word to explain
        stream: If True, return a generator that yields text chunks
        text_model: 'mistral', 'deepseek', or 'gemini'

    Returns:
        str or generator: Full explanation text or generator of text chunks
    """
    if text_model == 'deepseek':
        return _explain_word_deepseek(word, stream)
    elif text_model == 'gemini':
        return _explain_word_gemini(word, stream)
    else:
        return _explain_word_mistral(word, stream)

def _explain_word_mistral(word, stream=False):
    """Generate explanation using Mistral API."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return "Error: MISTRAL_API_KEY not found in environment variables."

    url = "https://api.mistral.ai/v1/chat/completions"

    system_prompt = """You are an expert English vocabulary teacher and etymologist. For the English word I provide, give a clear, accurate, and engaging explanation using ONLY English and exactly the following structure (do not add extra sections or headings):

Word: [the word in bold]

Etymology & Word Origins:
[Explain the word's roots, origin language(s), prefix/suffix if any, and how the meaning evolved. Keep it concise but fascinating.]

Phonetic Transcription:
[Provide the IPA transcription in brackets, e.g., /wɜːrd/]

Definition(s):
1. [Primary meaning]
2. [Secondary meaning if relevant]

Synonyms:
[list 4–6 useful synonyms]

Antonyms (if applicable):
[list 2–4 antonyms]

Example Sentences:
1. [Simple sentence]
2. [More advanced/contextual sentence]
3. [Idiomatic or literary use if relevant]

Writing (approximately 80 words):
[Write an original, natural paragraph/story of about 100 words that meaningfully uses the target word at least twice (bold the word each time it appears) to show its nuance and collocations.]"""

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The word is: {word}"}
        ],
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if stream:
        return _stream_response(url, payload, headers)
    else:
        return _sync_response(url, payload, headers)

def _explain_word_deepseek(word, stream=False):
    """Generate explanation using DeepSeek API (OpenAI compatible)."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "Error: DEEPSEEK_API_KEY not found in environment variables."

    url = "https://api.deepseek.com/chat/completions"

    system_prompt = """You are an expert English vocabulary teacher and etymologist. For the English word I provide, give a clear, accurate, and engaging explanation using ONLY English and exactly the following structure (do not add extra sections or headings):

Word: [the word in bold]

Etymology & Word Origins:
[Explain the word's roots, origin language(s), prefix/suffix if any, and how the meaning evolved. Keep it concise but fascinating.]

Phonetic Transcription:
[Provide the IPA transcription in brackets, e.g., /wɜːrd/]

Definition(s):
1. [Primary meaning]
2. [Secondary meaning if relevant]

Synonyms:
[list 4–6 useful synonyms]

Antonyms (if applicable):
[list 2–4 antonyms]

Example Sentences:
1. [Simple sentence]
2. [More advanced/contextual sentence]
3. [Idiomatic or literary use if relevant]

Writing (approximately 80 words):
[Write an original, natural paragraph/story of about 100 words that meaningfully uses the target word at least twice (bold the word each time it appears) to show its nuance and collocations.]"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The word is: {word}"}
        ],
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if stream:
        return _stream_response(url, payload, headers)
    else:
        return _sync_response(url, payload, headers)

def _explain_word_gemini(word, stream=False):
    """Generate explanation using Google Gemini API (Vertex AI or API Key mode)."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        error_msg = "Error: google-genai package not installed. Please install it with: pip install google-genai"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    # Check for Vertex AI configuration
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    location = os.environ.get("GOOGLE_LOCATION", "global")
    api_key = os.environ.get("GOOGLE_API_KEY")

    # Determine which mode to use
    use_vertexai = project_id and project_id != "YOUR_PROJECT_ID"

    try:
        if use_vertexai:
            # Vertex AI mode
            print(f"[Gemini] Using Vertex AI mode (Project: {project_id}, Location: {location})")
            client = genai.Client(vertexai=True, project=project_id, location=location)
            model = "gemini-2.5-flash"
        else:
            # API Key mode
            if not api_key:
                error_msg = "Error: GOOGLE_API_KEY not found in environment variables."
                if stream:
                    def error_gen():
                        yield error_msg
                    return error_gen()
                return error_msg

            print(f"[Gemini] Using API Key mode")
            client = genai.Client(api_key=api_key)
            model = "gemini-2.0-flash-exp"

    except Exception as e:
        error_msg = f"Error initializing Gemini client: {e}"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    system_prompt = """You are an expert English vocabulary teacher and etymologist. For the English word I provide, give a clear, accurate, and engaging explanation using ONLY English and exactly the following structure (do not add extra sections or headings):

Word: [the word in bold]

Etymology & Word Origins:
[Explain the word's roots, origin language(s), prefix/suffix if any, and how the meaning evolved. Keep it concise but fascinating.]

Phonetic Transcription:
[Provide the IPA transcription in brackets, e.g., /wɜːrd/]

Definition(s):
1. [Primary meaning]
2. [Secondary meaning if relevant]

Synonyms:
[list 4–6 useful synonyms]

Antonyms (if applicable):
[list 2–4 antonyms]

Example Sentences:
1. [Simple sentence]
2. [More advanced/contextual sentence]
3. [Idiomatic or literary use if relevant]

Writing (approximately 80 words):
[Write an original, natural paragraph/story of about 100 words that meaningfully uses the target word at least twice (bold the word each time it appears) to show its nuance and collocations.]"""

    try:
        if stream:
            # Streaming mode
            def stream_generator():
                try:
                    response = client.models.generate_content_stream(
                        model=model,
                        contents=f"{system_prompt}\n\nThe word is: {word}"
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                except Exception as e:
                    yield f"Error during streaming: {e}"

            return stream_generator()
        else:
            # Non-streaming mode
            response = client.models.generate_content(
                model=model,
                contents=f"{system_prompt}\n\nThe word is: {word}"
            )
            return response.text

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
        error_msg = f"HTTP Error {e.code}: {error_body}"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg
    except Exception as e:
        error_msg = f"Error calling Gemini API: {e}"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

# =============================================================================
# Chat Functions
# =============================================================================

def chat_with_ai(user_message, stream=False, text_model='mistral'):
    """Chat with the AI using specified text model.

    Args:
        user_message: User's message
        stream: If True, return a generator that yields text chunks
        text_model: 'mistral', 'deepseek', or 'gemini'

    Returns:
        str or generator: Full response text or generator of text chunks
    """
    if text_model == 'deepseek':
        return _chat_deepseek(user_message, stream)
    elif text_model == 'gemini':
        return _chat_gemini(user_message, stream)
    else:
        return _chat_mistral(user_message, stream)

def _chat_mistral(user_message, stream=False):
    """Chat using Mistral API."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return "Error: MISTRAL_API_KEY not found."

    url = "https://api.mistral.ai/v1/chat/completions"

    system_prompt = """You are a friendly and helpful English language tutor for international students.

CRITICAL RULES:
1. ALWAYS respond in English, regardless of what language the user uses
2. If the user writes in Chinese, Spanish, French, or any other language, respond in English
3. Help users practice English conversation naturally
4. Keep responses concise (2-3 sentences) and encouraging
5. Use simple, clear English that's easy to understand

Your goal is to help users practice English conversation in a natural, supportive way.
6. Do NOT use emojis or icons."""

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if stream:
        return _stream_response(url, payload, headers)
    else:
        return _sync_response(url, payload, headers)

def _chat_deepseek(user_message, stream=False):
    """Chat using DeepSeek API."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "Error: DEEPSEEK_API_KEY not found."

    url = "https://api.deepseek.com/chat/completions"

    system_prompt = """You are a friendly and helpful English language tutor for international students.

CRITICAL RULES:
1. ALWAYS respond in English, regardless of what language the user uses
2. If the user writes in Chinese, Spanish, French, or any other language, respond in English
3. Help users practice English conversation naturally
4. Keep responses concise (2-3 sentences) and encouraging
5. Use simple, clear English that's easy to understand

Your goal is to help users practice English conversation in a natural, supportive way.
6. Do NOT use emojis or icons."""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if stream:
        return _stream_response(url, payload, headers)
    else:
        return _sync_response(url, payload, headers)

def _chat_gemini(user_message, stream=False):
    """Chat using Google Gemini API (Vertex AI or API Key mode)."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        error_msg = "Error: google-genai package not installed. Please install it with: pip install google-genai"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    # Check for Vertex AI configuration
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    location = os.environ.get("GOOGLE_LOCATION", "global")
    api_key = os.environ.get("GOOGLE_API_KEY")

    # Determine which mode to use
    use_vertexai = project_id and project_id != "YOUR_PROJECT_ID"

    try:
        if use_vertexai:
            # Vertex AI mode
            print(f"[Gemini Chat] Using Vertex AI mode (Project: {project_id}, Location: {location})")
            client = genai.Client(vertexai=True, project=project_id, location=location)
            model = "gemini-2.5-flash"
        else:
            # API Key mode
            if not api_key:
                error_msg = "Error: GOOGLE_API_KEY not found in environment variables."
                if stream:
                    def error_gen():
                        yield error_msg
                    return error_gen()
                return error_msg

            print(f"[Gemini Chat] Using API Key mode")
            client = genai.Client(api_key=api_key)
            model = "gemini-2.0-flash-exp"

    except Exception as e:
        error_msg = f"Error initializing Gemini client: {e}"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

    system_prompt = """You are a friendly and helpful English language tutor for international students.

CRITICAL RULES:
1. ALWAYS respond in English, regardless of what language the user uses
2. If the user writes in Chinese, Spanish, French, or any other language, respond in English
3. Help users practice English conversation naturally
4. Keep responses concise (2-3 sentences) and encouraging
5. Use simple, clear English that's easy to understand

Your goal is to help users practice English conversation in a natural, supportive way.
6. Do NOT use emojis or icons."""

    try:
        if stream:
            # Streaming mode
            def stream_generator():
                try:
                    response = client.models.generate_content_stream(
                        model=model,
                        contents=f"{system_prompt}\n\nUser: {user_message}"
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                except Exception as e:
                    yield f"Error during streaming: {e}"

            return stream_generator()
        else:
            # Non-streaming mode
            response = client.models.generate_content(
                model=model,
                contents=f"{system_prompt}\n\nUser: {user_message}"
            )
            return response.text

    except Exception as e:
        error_msg = f"Error calling Gemini API: {e}"
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg

if __name__ == "__main__":
    # Load environment variables
    load_env_vars()

    # Get a random word
    print("Fetching random word...")
    word = get_random_word()
    print(f"Selected word: {word}")

    if "Error" in word or "No words" in word:
        print(word)
    else:
        print("\nGenerating explanation...\n")
        explanation = explain_word(word)
        print(explanation)
