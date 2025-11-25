#!/usr/bin/env python3
"""
Gemini Imagen API 图片生成测试程序

功能：
- 从 .env 文件读取 GOOGLE_API_KEY 或 GEMINI_API_KEY
- 使用 Gemini Imagen API 生成图片
- 保存到 test_output 目录
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from explain_word import load_env_vars

# 尝试导入 Gemini API
try:
    from google import genai
    from google.genai import types
    print("✓ google-genai package imported successfully")
except ImportError as e:
    print(f"✗ Error: google-genai package not installed")
    print(f"  Please install it with: pip install google-genai")
    sys.exit(1)


def test_gemini_image_generation(prompt, output_filename="test_gemini_output.png"):
    """
    测试 Gemini Imagen API 图片生成

    Args:
        prompt: 图片生成提示词
        output_filename: 输出文件名

    Returns:
        bool: 成功返回 True，失败返回 False
    """
    # 加载环境变量
    print("\n" + "="*60)
    print("Step 1: Loading environment variables...")
    print("="*60)
    load_env_vars()

    # 检查 API Key（支持两种命名）
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("✗ Error: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment")
        print("  Please check your .env file")
        return False

    print(f"✓ API Key found: {api_key[:20]}...")

    # 创建输出目录
    output_dir = project_root / "test_output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / output_filename

    print("\n" + "="*60)
    print("Step 2: Initializing Gemini client...")
    print("="*60)

    try:
        client = genai.Client(api_key=api_key)
        print("✓ Gemini client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    print("\n" + "="*60)
    print("Step 3: Generating image...")
    print("="*60)
    print(f"Prompt: {prompt}")
    print(f"Model: imagen-4.0-generate-001")
    print(f"Aspect ratio: 16:9")

    try:
        # 生成图片
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='16:9',
                safety_filter_level='block_low_and_above',
                person_generation='allow_adult'
            )
        )

        print("✓ Image generation request completed")

    except Exception as e:
        error_msg = str(e)
        print(f"\n✗ Image generation failed:")
        print(f"  Error: {error_msg}")

        # 检查是否是地理限制错误
        if 'location is not supported' in error_msg.lower() or 'FAILED_PRECONDITION' in error_msg:
            print("\n  ⚠️  Geographic Restriction Detected")
            print("  This error means Gemini Imagen API is not available in your region.")
            print("  The service may be restricted in China or your current location.")

        return False

    print("\n" + "="*60)
    print("Step 4: Saving image...")
    print("="*60)

    try:
        # 检查是否生成了图片
        if not response.generated_images or len(response.generated_images) == 0:
            print("✗ No images generated in response")
            return False

        # 获取第一张图片
        generated_image = response.generated_images[0]

        # 保存图片
        if hasattr(generated_image.image, '_pil_image'):
            pil_image = generated_image.image._pil_image
            pil_image.save(output_path, format='PNG')
        else:
            # 备用方法：使用图片字节
            image_bytes = generated_image.image._image_bytes
            with open(output_path, 'wb') as f:
                f.write(image_bytes)

        print(f"✓ Image saved successfully!")
        print(f"  Path: {output_path}")
        print(f"  Size: {output_path.stat().st_size} bytes")

        return True

    except Exception as e:
        print(f"✗ Failed to save image: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Gemini Imagen API 图片生成测试")
    print("="*60)

    # 测试提示词
    test_prompts = [
        {
            "prompt": "A beautiful sunset over mountains with vibrant orange and purple colors",
            "filename": "test_sunset.png"
        },
        {
            "prompt": "An anime-style illustration of a happy cat reading a book in a cozy library",
            "filename": "test_anime_cat.png"
        },
        {
            "prompt": "Abstract representation of the English word 'serene' - peaceful blue water with gentle ripples",
            "filename": "test_serene.png"
        }
    ]

    # 让用户选择测试
    print("\nAvailable test prompts:")
    for i, item in enumerate(test_prompts, 1):
        print(f"  {i}. {item['prompt'][:60]}...")
    print(f"  4. Custom prompt")

    try:
        choice = input("\nSelect prompt (1-4, or Enter for default): ").strip()

        if not choice:
            # 默认使用第一个
            selected = test_prompts[0]
        elif choice == '4':
            # 自定义提示词
            custom_prompt = input("Enter your prompt: ").strip()
            if not custom_prompt:
                print("Empty prompt, using default")
                selected = test_prompts[0]
            else:
                selected = {
                    "prompt": custom_prompt,
                    "filename": "test_custom.png"
                }
        else:
            # 选择预设提示词
            idx = int(choice) - 1
            if 0 <= idx < len(test_prompts):
                selected = test_prompts[idx]
            else:
                print("Invalid choice, using default")
                selected = test_prompts[0]

    except (ValueError, KeyboardInterrupt):
        print("\nUsing default prompt")
        selected = test_prompts[0]

    # 执行测试
    success = test_gemini_image_generation(
        prompt=selected["prompt"],
        output_filename=selected["filename"]
    )

    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED - Image generated successfully!")
        print("="*60)
        return 0
    else:
        print("❌ TEST FAILED - Image generation failed")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
