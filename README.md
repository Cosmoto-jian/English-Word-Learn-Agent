# AI Word Master

An intelligent English vocabulary learning agent that generates interactive word cards with AI-powered explanations, anime-style images, natural audio pronunciation, and leverages state-of-the-art AI models for English conversation.

**🚀 [Live Demo](https://english-word-learn-agent.onrender.com)** | **📱 [Mobile Access](https://english-word-learn-agent.onrender.com)** | **💻 [GitHub](https://github.com/Cosmoto-jian/English-Word-Learn-Agent)**

> **Note:** First visit may take 10-30 seconds to load (free tier cold start)

## Features

- **Multi-Model AI Support**: Choose between Mistral AI, DeepSeek, or Google Gemini for text generation
- **Dual Audio Providers**: Amazon Polly or Deepgram TTS with multiple voice options
- **AI Image Generation**: Google Gemini Imagen generates anime-style contextual images
- **Vocabulary Levels**: Select from junior, senior, cet4, cet6, gre, ielts, sat, toefl levels
- **Interactive Chat**: Practice English conversation with AI tutor (multilingual input, English output)
- **Streaming Response**: Real-time text streaming for smooth user experience
- **Image Caching**: Optimized image storage for faster repeat word lookups
- **Phonetic Display**: IPA transcription with audio playback
- **Social Integration**: Quick access to social media platforms

## Demo

**🌐 [Try it Live!](https://english-word-learn-agent.onrender.com)**

![AI Word Master Demo](static/demo.png)

## Tech Stack

| Component | Technology | Options |
|-----------|------------|---------|
| Backend | Flask (Python) | - |
| AI Text Generation | Multi-provider | Mistral AI / DeepSeek / Google Gemini |
| Text-to-Speech | Dual-provider | Amazon Polly (Neural) / Deepgram TTS |
| Image Generation | Google Gemini | Imagen 4.0 (API Key / Vertex AI) |
| Concurrency | ThreadPoolExecutor | Parallel resource generation |
| Streaming | Server-Sent Events (SSE) | Real-time chat |

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd AWS-English-academic-presetation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Text Generation APIs (choose one or more)
MISTRAL_API_KEY=your_mistral_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GOOGLE_API_KEY=your_google_api_key

# Google Cloud Configuration for Vertex AI (optional)
GOOGLE_PROJECT_ID=YOUR_PROJECT_ID
GOOGLE_LOCATION=global

# Audio Generation APIs
DEEPGRAM_API_KEY=your_deepgram_api_key

# AWS Configuration (for Amazon Polly)
AWS_PROFILE=EAP001
AWS_REGION=us-east-1

# Server Configuration
PORT=5500
HOST=127.0.0.1
```

### 4. Configure AWS Credentials (for Amazon Polly)

Create or edit `~/.aws/credentials`:

```ini
[EAP001]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = us-east-1
```

**Required IAM Policy**: `AmazonPollyFullAccess`

### 5. Run the Application

```bash
python server.py
```

Or use the startup script:

```bash
./start.sh
```

Visit: http://127.0.0.1:5500

## Usage

### Generate Word Card

1. (Optional) Select vocabulary level from dropdown (junior, senior, cet4, cet6, gre, ielts, sat, toefl)
2. (Optional) Select text model (Mistral, DeepSeek, or Gemini)
3. (Optional) Select audio model (Polly or Deepgram)
4. (Optional) Select voice (Joanna, Matthew, or Salli)
5. Enter a word in the input field (or leave empty for random word)
6. Click "Start Learning"
7. Wait for the card to generate (~15-20 seconds)
8. Click the speaker icons to play audio
9. Click the phonetic transcription play button to hear pronunciation

### Chat with AI

1. Type any message in the chat box (any language supported)
2. AI will respond in English with streaming output
3. Click the speaker icon to hear the response

### Flip for New Word

Click the refresh button (bottom right) to generate a new random word card.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/api/voices` | GET | Get available voice options |
| `/api/levels` | GET | Get available vocabulary levels |
| `/api/models` | GET | Get available AI models |
| `/api/generate` | POST | Generate word card |
| `/api/chat/stream` | POST | Streaming chat endpoint |
| `/static/<path>` | GET | Serve static files (audio, JS) |
| `/public/<path>` | GET | Serve cached images |

### Example: Generate Word Card

```bash
curl -X POST http://localhost:5500/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "word": "serendipity",
    "voice_id": "Joanna",
    "level": "gre",
    "text_model": "gemini",
    "audio_model": "polly"
  }'
```

### Example: Chat with AI

```bash
curl -X POST http://localhost:5500/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I use this word?",
    "voice_id": "Matthew",
    "text_model": "mistral",
    "audio_model": "deepgram"
  }'
```

## Project Structure

```
AWS-English-academic-presetation/
├── server.py              # Flask application with port management
├── generate_card.py       # Card generation orchestrator
├── generate_audio.py      # Multi-provider TTS (Polly/Deepgram)
├── generate_image.py      # Google Gemini Imagen integration
├── explain_word.py        # Multi-provider text generation
├── word.py                # Word selection by level
├── polly_api.py           # Polly CLI tool
├── templates/
│   └── index.html         # Main page with social icons
├── static/
│   ├── style.css          # Glass morphism styles
│   ├── script.js          # Frontend logic with audio toggle
│   └── GridArrayBg.module.js  # Animated background
├── public/
│   └── generate_picture/  # Cached generated images
├── scripts/
│   ├── create_json.py     # Vocabulary level JSON generator
│   └── gen.sh             # Batch generation script
├── words_dictionary.json  # Full word database (370k+ words)
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (create this)
```

## Configuration

### Available Vocabulary Levels

| Level ID | Description | Word Count |
|----------|-------------|------------|
| junior | Junior high school | ~2,000 |
| senior | Senior high school | ~3,500 |
| cet4 | College English Test 4 | ~4,500 |
| cet6 | College English Test 6 | ~6,000 |
| gre | GRE exam vocabulary | ~8,000 |
| ielts | IELTS exam vocabulary | ~7,000 |
| sat | SAT exam vocabulary | ~5,000 |
| toefl | TOEFL exam vocabulary | ~8,000 |

### Available Voices (Amazon Polly)

| Voice ID | Name | Gender | Accent |
|----------|------|--------|--------|
| Joanna | Joanna (Female, US) | Female | American |
| Matthew | Matthew (Male, US) | Male | American |
| Salli | Salli (Female, US) | Female | American |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | Conditional | Mistral AI API key (if using Mistral) |
| `DEEPSEEK_API_KEY` | Conditional | DeepSeek API key (if using DeepSeek) |
| `GOOGLE_API_KEY` | Conditional | Google API key (if using Gemini API Key mode) |
| `GOOGLE_PROJECT_ID` | Conditional | Google Cloud project ID (if using Vertex AI) |
| `GOOGLE_LOCATION` | No | Google Cloud location (default: global) |
| `DEEPGRAM_API_KEY` | Conditional | Deepgram API key (if using Deepgram TTS) |
| `AWS_PROFILE` | No | AWS profile name (default: EAP001) |
| `AWS_REGION` | No | AWS region (default: us-east-1) |
| `PORT` | No | Server port (default: 5500) |
| `HOST` | No | Server host (default: 127.0.0.1) |

## Performance

| Operation | Time |
|-----------|------|
| Text generation (Gemini) | ~4-6s |
| Image generation (Gemini) | ~8-12s |
| Word audio (Polly) | ~0.5s |
| Explanation audio (Polly) | ~2s |
| **Total (parallel)** | **~12-15s** |

### Optimizations

- **Parallel resource generation**: Image and audio generated simultaneously (3x faster)
- **Streaming text response**: 84% latency reduction for user perception
- **Image caching**: Word-based filenames in `public/generate_picture/` for instant re-access
- **Local word dictionary**: Offline capable, no API calls for word selection
- **Async audio generation**: Non-blocking chat audio creation

## Google Gemini Configuration

The application supports two modes for Google Gemini:

### 1. API Key Mode (Simpler)
- **Text Model**: `gemini-2.0-flash-exp`
- **Image Model**: `imagen-4.0-generate-001`
- **Setup**: Just add `GOOGLE_API_KEY` to `.env`

### 2. Vertex AI Mode (Enterprise)
- **Text Model**: `gemini-2.5-flash`
- **Image Model**: `gemini-2.5-flash-image-preview`
- **Setup**: Configure `GOOGLE_PROJECT_ID` and `GOOGLE_LOCATION` in `.env`

The system automatically detects which mode to use based on environment variables.

## Troubleshooting

### AWS Credentials Error

```
Error: AWS credentials not found
```

**Solution**: Configure `~/.aws/credentials` with your AWS access keys.

### Polly Permission Error

```
AccessDeniedException: User is not authorized to perform: polly:SynthesizeSpeech
```

**Solution**: Add `AmazonPollyFullAccess` policy to your IAM user.

### Missing API Keys

```
Missing API keys for selected models: GOOGLE_API_KEY or GOOGLE_PROJECT_ID
```

**Solution**: Add the required API key to your `.env` file based on which model you want to use.

### Port Already in Use

The server includes automatic port management:
- Detects if port is in use
- Attempts to kill old server.py processes
- Automatically finds alternative port if needed

## Features in Detail

### Glass Morphism UI
- Modern translucent design with backdrop blur
- Smooth animations and transitions
- Social media icons with hover effects

### Phonetic Transcription
- IPA format display: `[/wɜːrd/]`
- Positioned below word title
- Play button for pronunciation

### Audio Controls
- Play/pause toggle functionality
- Icon switching (play ↔ pause)
- Automatic resource cleanup

### Image Caching Strategy
- Filename based on sanitized word
- Stored in `public/generate_picture/`
- Instant loading for previously generated words
- Reduces API calls and generation time

## Deployment

### Deploy to Render (Recommended)

This application is deployed on [Render](https://render.com) with the following configuration:

**Live URL:** https://english-word-learn-agent.onrender.com

#### Quick Deploy Steps:

1. **Fork or clone this repository**
2. **Sign up on [Render](https://render.com)** with your GitHub account
3. **Create a new Web Service** and connect your repository
4. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 server:app`
5. **Add environment variables** (at least one text model and one audio model):
   ```
   GOOGLE_API_KEY=your_key
   DEEPGRAM_API_KEY=your_key
   ```
6. **Deploy!** Render will automatically build and deploy your app

#### Free Tier Limitations:
- 15-minute idle timeout (app sleeps after inactivity)
- 512 MB RAM
- Temporary file storage (generated files reset on restart)

For production use, consider upgrading to a paid plan for:
- Always-on service (no cold starts)
- Persistent storage
- More resources

### Alternative Platforms:
- **Vercel**: Good for frontend, limited for long-running tasks
- **Railway**: Similar to Render, easy deployment
- **Fly.io**: Global edge deployment
- **Heroku**: Classic PaaS platform

## License

This project is for educational purposes.

Word list data sourced from [english-words](https://github.com/dwyl/english-words).

## Acknowledgments

- [Mistral AI](https://mistral.ai/) - Text generation
- [DeepSeek](https://www.deepseek.com/) - Text generation
- [Google Gemini](https://ai.google.dev/) - Text and image generation
- [Amazon Polly](https://aws.amazon.com/polly/) - Text-to-speech
- [Deepgram](https://deepgram.com/) - Text-to-speech
- [dwyl/english-words](https://github.com/dwyl/english-words) - Word dictionary
