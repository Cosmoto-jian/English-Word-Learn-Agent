import os
import boto3
import json
import urllib.request
import urllib.error
from botocore.exceptions import ClientError, NoCredentialsError
from contextlib import closing
from word import get_random_word
from explain_word import explain_word, load_env_vars

def generate_audio(text, filename, voice_id='Joanna', audio_model='polly'):
    """Generate audio from text using specified TTS model.

    Args:
        text: Text to convert to speech
        filename: Output filename (full path)
        voice_id: Voice ID for the TTS model
        audio_model: 'polly' or 'deepgram' (default: polly)

    Returns:
        bool: True if successful, False otherwise
    """
    if audio_model == 'deepgram':
        return _generate_audio_deepgram(text, filename, voice_id)
    else:
        return _generate_audio_polly(text, filename, voice_id)

def _generate_audio_polly(text, filename, voice_id='Joanna', engine='neural'):
    """Generate audio using Amazon Polly API.

    Args:
        text: Text to convert to speech
        filename: Output filename (full path)
        voice_id: Polly voice ID (default: Joanna)
        engine: Engine type - 'neural' or 'standard' (default: neural)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not text or not text.strip():
            print("Error: Empty text provided for audio generation")
            return False

        # Initialize Polly client
        # Support both local (profile) and cloud (env vars) authentication
        region = os.environ.get("AWS_REGION", "us-east-1")

        # Check if AWS credentials are provided via environment variables (cloud deployment)
        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

        if aws_access_key and aws_secret_key:
            # Use environment variables (for cloud deployment like Render)
            print(f"Using AWS credentials from environment variables")
            session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
        else:
            # Use profile (for local development)
            profile_name = os.environ.get("AWS_PROFILE", "EAP001")
            print(f"Using AWS profile: {profile_name}")
            session = boto3.Session(profile_name=profile_name)

        polly = session.client('polly', region_name=region)

        # Ensure filename is absolute
        if not os.path.isabs(filename):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, filename)

        # Prepare request parameters
        params = {
            'Text': text,
            'OutputFormat': 'mp3',
            'VoiceId': voice_id,
            'Engine': engine
        }

        print(f"Generating audio with Polly (voice: {voice_id}, engine: {engine})...")
        print(f"Text length: {len(text)}")
        print(f"Output file: {filename}")

        # Call Polly API
        response = polly.synthesize_speech(**params)

        # Save audio stream to file
        if 'AudioStream' in response:
            with closing(response['AudioStream']) as stream:
                with open(filename, 'wb') as f:
                    audio_data = stream.read()
                    f.write(audio_data)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force OS to write to disk
                    print(f"Audio saved to {filename} ({len(audio_data)} bytes)")

            # Verify file was created and has content
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"✅ Audio file verified: {os.path.getsize(filename)} bytes")
                return True
            else:
                print(f"❌ Error: File not found or empty after write: {filename}")
                return False
        else:
            print("Error: No AudioStream in Polly response")
            return False

    except NoCredentialsError:
        print(f"Error: AWS credentials not found. Please configure profile '{profile_name}'")
        return False
    except ClientError as e:
        print(f"Error: AWS Polly API error: {e}")
        return False
    except Exception as e:
        print(f"Error generating audio: {e}")
        import traceback
        traceback.print_exc()
        return False

def _generate_audio_deepgram(text, filename, voice_id='aura-asteria-en'):
    """Generate audio using Deepgram API.

    Args:
        text: Text to convert to speech
        filename: Output filename (full path)
        voice_id: Deepgram voice model (default: aura-asteria-en)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not text or not text.strip():
            print("Error: Empty text provided for audio generation")
            return False

        api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not api_key:
            print("Error: DEEPGRAM_API_KEY not found in environment variables")
            return False

        # Ensure filename is absolute
        if not os.path.isabs(filename):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, filename)

        url = f"https://api.deepgram.com/v1/speak?model={voice_id}"

        payload = json.dumps({"text": text})
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }

        print(f"Generating audio with Deepgram (voice: {voice_id})...")
        print(f"Text length: {len(text)}")
        print(f"Output file: {filename}")

        # Call Deepgram API
        req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            audio_data = response.read()

            # Save audio to file
            with open(filename, 'wb') as f:
                f.write(audio_data)
                f.flush()
                os.fsync(f.fileno())
                print(f"Audio saved to {filename} ({len(audio_data)} bytes)")

        # Verify file was created and has content
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"✅ Audio file verified: {os.path.getsize(filename)} bytes")
            return True
        else:
            print(f"❌ Error: File not found or empty after write: {filename}")
            return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        print(f"HTTP Error: {e.code} {e.reason}\n{error_body}")
        return False
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Error generating audio: {e}")
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
        # 2. Generate audio for the word
        print(f"Generating audio for word: {word}")
        generate_audio(word, "word_audio.mp3")

        # 3. Get explanation
        print("\nGenerating explanation...")
        explanation = explain_word(word)

        if explanation and not explanation.startswith("Error"):
            print("Explanation generated.")
            # 4. Generate audio for the explanation
            print("Generating audio for explanation...")
            generate_audio(explanation, "explanation_audio.mp3")
        else:
            print(f"Failed to generate explanation: {explanation}")
