#!/usr/bin/env python3
"""
Amazon Polly 语音合成 API
支持多种语音、格式和高级功能
"""

import boto3
import argparse
import sys
import os
import json
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError
from contextlib import closing
import subprocess
from datetime import datetime

class PollyAPI:
    def __init__(self, profile_name='EAP001', region='us-east-1'):
        """初始化 Polly API 客户端"""
        try:
            # 使用您的配置文件
            session = boto3.Session(profile_name=profile_name)
            self.polly = session.client('polly', region_name=region)
            self.profile_name = profile_name
            self.region = region

            # 验证连接
            self.polly.describe_voices()
            print(f"✅ 成功连接到 AWS Polly (配置文件: {profile_name})")

        except NoCredentialsError:
            print(f"❌ 错误：找不到配置文件 '{profile_name}'")
            sys.exit(1)
        except ClientError as e:
            print(f"❌ AWS 连接错误: {e}")
            sys.exit(1)

    def synthesize_speech(self, text, voice_id='Joanna', engine='neural',
                         output_format='mp3', output_file=None, language_code=None):
        """
        合成语音

        参数:
        - text: 要转换的文本
        - voice_id: 语音 ID
        - engine: 引擎类型 (standard/neural)
        - output_format: 输出格式 (mp3/ogg_vorbis/pcm)
        - output_file: 输出文件路径
        - language_code: 语言代码（双语语音使用）
        """
        try:
            # 构建请求参数
            params = {
                'Text': text,
                'OutputFormat': output_format,
                'VoiceId': voice_id,
                'Engine': engine
            }

            if language_code:
                params['LanguageCode'] = language_code

            print(f"🎯 正在合成语音...")
            print(f"   文本: {text[:50]}{'...' if len(text) > 50 else ''}")
            print(f"   语音: {voice_id}")
            print(f"   引擎: {engine}")
            print(f"   格式: {output_format}")

            # 调用 Polly API
            response = self.polly.synthesize_speech(**params)

            # 处理输出文件名
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"speech_{voice_id}_{timestamp}.{output_format}"

            # 保存音频文件
            with closing(response['AudioStream']) as stream:
                with open(output_file, 'wb') as file:
                    file.write(stream.read())

            print(f"✅ 语音合成成功！")
            print(f"📁 文件保存至: {os.path.abspath(output_file)}")

            return output_file

        except ClientError as e:
            print(f"❌ 语音合成失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 文件保存失败: {e}")
            return None

    def list_voices(self, language_code=None, engine=None):
        """列出可用的语音"""
        try:
            params = {}
            if language_code:
                params['LanguageCode'] = language_code
            if engine:
                params['Engine'] = engine

            response = self.polly.describe_voices(**params)
            voices = response.get('Voices', [])

            print(f"\n🎤 可用语音 ({len(voices)} 个):")
            print("-" * 80)
            print(f"{'ID':<15} {'性别':<6} {'语言':<20} {'引擎':<15} {'语言代码'}")
            print("-" * 80)

            for voice in voices:
                voice_id = voice['Id']
                gender = voice.get('Gender', 'Unknown')
                language = voice.get('LanguageName', 'Unknown')
                engines = ', '.join(voice.get('SupportedEngines', []))
                lang_code = voice.get('LanguageCode', 'Unknown')

                print(f"{voice_id:<15} {gender:<6} {language:<20} {engines:<15} {lang_code}")

            return voices

        except ClientError as e:
            print(f"❌ 获取语音列表失败: {e}")
            return []

    def batch_synthesize(self, texts, voice_id='Joanna', engine='neural',
                        output_dir='./batch_output'):
        """批量合成语音"""
        Path(output_dir).mkdir(exist_ok=True)
        results = []

        print(f"🔄 开始批量合成 {len(texts)} 个文本...")

        for i, text in enumerate(texts, 1):
            print(f"\n[{i}/{len(texts)}] 处理中...")
            output_file = Path(output_dir) / f"batch_{i:03d}_{voice_id}.mp3"

            result = self.synthesize_speech(
                text=text,
                voice_id=voice_id,
                engine=engine,
                output_file=str(output_file)
            )

            results.append({
                'index': i,
                'text': text,
                'file': result,
                'success': result is not None
            })

        # 生成批量处理报告
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 批量处理完成:")
        print(f"   成功: {success_count}/{len(texts)}")
        print(f"   输出目录: {os.path.abspath(output_dir)}")

        return results

    def play_audio(self, file_path):
        """播放音频文件"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False

            print(f"🔊 正在播放: {file_path}")

            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])

            return True

        except Exception as e:
            print(f"⚠️  播放失败: {e}")
            return False

    def get_voice_info(self, voice_id):
        """获取特定语音的详细信息"""
        try:
            voices = self.list_voices()
            for voice in voices:
                if voice['Id'] == voice_id:
                    print(f"\n🎤 语音信息: {voice_id}")
                    print(f"   性别: {voice.get('Gender')}")
                    print(f"   语言: {voice.get('LanguageName')} ({voice.get('LanguageCode')})")
                    print(f"   支持引擎: {', '.join(voice.get('SupportedEngines', []))}")
                    return voice

            print(f"❌ 未找到语音: {voice_id}")
            return None

        except Exception as e:
            print(f"❌ 获取语音信息失败: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(
        description='Amazon Polly 语音合成 API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本语音合成
  python polly_api.py "Hello, world!"

  # 使用中文语音
  python polly_api.py "你好世界" --voice Zhiyu --engine neural

  # 合成后自动播放
  python polly_api.py "Testing audio" --play

  # 指定输出文件
  python polly_api.py "Custom output" --output my_speech.mp3

  # 列出所有语音
  python polly_api.py --list-voices

  # 列出中文语音
  python polly_api.py --list-voices --language zh-CN

  # 获取语音信息
  python polly_api.py --voice-info Joanna

  # 批量处理文本文件
  python polly_api.py --batch texts.txt --voice Joanna
        """
    )

    parser.add_argument('text', nargs='?', help='要转换为语音的文本')
    parser.add_argument('--voice', '-v', default='Joanna', help='语音 ID')
    parser.add_argument('--engine', '-e', choices=['standard', 'neural'],
                       default='neural', help='语音引擎')
    parser.add_argument('--format', '-f', choices=['mp3', 'ogg_vorbis', 'pcm'],
                       default='mp3', help='输出格式')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--language', help='语言代码 (如: zh-CN, en-US)')
    parser.add_argument('--play', '-p', action='store_true', help='合成后自动播放')
    parser.add_argument('--profile', default='EAP001', help='AWS 配置文件名')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS 区域')

    # 功能选项
    parser.add_argument('--list-voices', action='store_true', help='列出所有可用语音')
    parser.add_argument('--voice-info', help='获取指定语音的详细信息')
    parser.add_argument('--batch', help='批量处理文本文件')

    args = parser.parse_args()

    # 创建 Polly API 实例
    polly_api = PollyAPI(profile_name=args.profile, region=args.region)

    # 处理不同的功能
    if args.list_voices:
        polly_api.list_voices(language_code=args.language)
        return

    if args.voice_info:
        polly_api.get_voice_info(args.voice_info)
        return

    if args.batch:
        if not os.path.exists(args.batch):
            print(f"❌ 批量文件不存在: {args.batch}")
            sys.exit(1)

        with open(args.batch, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]

        polly_api.batch_synthesize(texts, voice_id=args.voice, engine=args.engine)
        return

    # 检查是否提供了文本
    if not args.text:
        parser.print_help()
        print("\n❌ 错误：请提供要转换的文本或使用其他功能选项")
        sys.exit(1)

    # 执行语音合成
    result = polly_api.synthesize_speech(
        text=args.text,
        voice_id=args.voice,
        engine=args.engine,
        output_format=args.format,
        output_file=args.output,
        language_code=args.language
    )

    # 播放音频（如果请求）
    if result and args.play:
        polly_api.play_audio(result)

if __name__ == "__main__":
    main()
