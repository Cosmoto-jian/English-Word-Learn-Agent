# AI Word Master
![AI Word Master](public/imgs/AIwordmaster.png)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open-brightgreen)](https://english-word-learn-agent.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)](https://github.com/Cosmoto-jian/English-Word-Learn-Agent)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE.md)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](#)

**让单词学习更有活力 — 输入任意单词进行听、说、读、写的全面练习，或选择一个单词本随机学习。**

本项目正在积极开发中，目前已接入 Google Gemini、DeepSeek 和 Mistral 等大模型，用于生成单词释义、例句与写作建议；并使用 Amazon Polly 生成自然发音与对话音频，未来计划加入实时语音转写等功能。

> **注意:** 首次访问可能因免费层冷启动而需要 3–4 分钟。

## 功能（Features）

- **词汇等级**：可从 junior、senior、cet4、cet6、gre、ielts、sat、toefl 中选择
- **互动聊天**：与 AI 导师练习英语会话（支持多语言输入，输出为英语）
- 本系统整合了多个大模型（Google Gemini、DeepSeek、Mistral）进行文本生成，支持 Amazon Polly 与 Deepgram 的神经 TTS，并使用 Google Gemini Imagen 为单词生成动漫风格的情境图片。

## 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
cd AWS-English-academic-presetation
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

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

### 4. 配置 AWS 凭证（用于 Amazon Polly）

创建或编辑 `~/.aws/credentials`：

```ini
[EAP001]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = us-east-1
```

**所需 IAM 策略**：`AmazonPollyFullAccess`

### 5. 运行应用

```bash
python server.py
```

或使用启动脚本：

```bash
./start.sh
```

访问： http://127.0.0.1:5500

## 使用说明（Usage）

### 生成单词卡

1.（可选）从下拉菜单选择词汇等级（junior、senior、cet4、cet6、gre、ielts、sat、toefl）
2.（可选）选择文本模型（Mistral、DeepSeek、Gemini）
3.（可选）选择音频模型（Polly 或 Deepgram）
4.（可选）选择声音（Joanna、Matthew、Salli 等）
5. 在输入栏输入单词（留空则随机）
6. 点击 “Start Learning”
7. 等待卡片生成（约 15–20 秒）
8. 点击扬声器图标播放音频
9. 点击音标播放按钮听发音

### 与 AI 聊天

1. 在聊天框输入任意消息（支持任意语言）
2. AI 将以英语进行流式输出回复
3. 点击扬声器图标收听语音

### 随机获取新单词

点击右下角刷新按钮以生成随机单词卡。

## 许可

本项目用于教育目的。

词表数据来源于 [dwyl/english-words](https://github.com/dwyl/english-words)。

## 致谢

- [Mistral AI](https://mistral.ai/) - 文本生成
- [DeepSeek](https://www.deepseek.com/) - 文本生成
- [Google Gemini](https://ai.google.dev/) - 文本与图像生成
- [Amazon Polly](https://aws.amazon.com/polly/) - 文字转语音
- [Deepgram](https://deepgram.com/) - 文字转语音
- [dwyl/english-words](https://github.com/dwyl/english-words) - 单词词典
