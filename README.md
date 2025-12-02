# AI Word Master
![AI Word Master](public/imgs/AIwordmaster.png)

<!-- Language navigation: jump to language sections -->
[![EN](https://img.shields.io/badge/EN-English-blue)](README.md) [![日本語](https://img.shields.io/badge/日本語-Japanese-orange)](README.ja.md) [![中文](https://img.shields.io/badge/中文-Chinese-red)](README.zh.md)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open-brightgreen)](https://english-word-learn-agent.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)](https://github.com/Cosmoto-jian/English-Word-Learn-Agent)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE.md)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](#)

**Make vocabulary learning come alive — enter any word for a complete listening, speaking, reading, and writing practice, or choose a word list to study words randomly.**

This project is under active development. It integrates Google Gemini, DeepSeek, and Mistral models to generate definitions, example sentences, and writing suggestions, and uses Amazon Polly for natural pronunciations and conversational audio. Real-time speech-to-text and additional features are planned.

> **Note:** First visit may take 3–4 minutes due to free‑tier cold starts.

## Features
- **Vocabulary Levels**: Select from junior, senior, cet4, cet6, gre, ielts, sat, toefl levels
- **Interactive Chat**: Practice English conversation with AI tutor (multilingual input, English output)
- The system integrates multiple large language models (Google Gemini, DeepSeek, and Mistral) for text generation, supports dual audio providers (Amazon Polly and Deepgram) for natural pronunciations and conversational audio, and uses Google Gemini Imagen to generate anime-style contextual images.

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
