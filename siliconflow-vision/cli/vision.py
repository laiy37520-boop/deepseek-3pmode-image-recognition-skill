#!/usr/bin/env python3
"""
Vision tool — describe an image via SiliconFlow compatible API.

Usage:
    python3 vision.py <image_path> [question]

Examples:
    python3 vision.py photo.jpg
    python3 vision.py screenshot.png "图片里有什么文字？"
    python3 vision.py chart.png "分析这个图表的数据趋势"

Environment variables:
    SILICONFLOW_API_KEY  你的 SiliconFlow API Key（必填）
                         获取地址: https://cloud.siliconflow.cn/account/ak

    SILICONFLOW_BASE_URL  API 地址（可选，默认 https://api.siliconflow.cn/v1）
                         如果你使用其他兼容 OpenAI SDK 的服务，可以修改此项

    VISION_MODEL          视觉模型名称（可选）
                          默认: Qwen/Qwen3-VL-8B-Instruct
                          其他选项:
                            - Qwen/Qwen3-VL-235B-A22B-Instruct（旗舰版）
                            - Qwen/Qwen2.5-VL-72B-Instruct（大杯）
                            - Qwen/Qwen2.5-VL-7B-Instruct（最快速）
                            - glm-4/glm-4.6v
                            - deepseek-ai/deepseek-vl2
"""
import sys
import base64
import mimetypes
import os
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 vision.py <image_path> [question]")
        print("")
        print("Environment variables:")
        print("  SILICONFLOW_API_KEY    SiliconFlow API Key (required)")
        print("  SILICONFLOW_BASE_URL   API base URL (optional)")
        print("  VISION_MODEL           Model name (optional)")
        sys.exit(1)

    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else (
        "请详细描述这张图片的内容，包括画面中的物体、人物、场景、文字、颜色等所有细节。"
    )

    # --- 检查 API Key ---
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        print("错误: 未设置 SILICONFLOW_API_KEY 环境变量")
        print("")
        print("请先设置你的 API Key：")
        print("  # Windows (PowerShell):")
        print('  $env:SILICONFLOW_API_KEY = "sk-你的key"')
        print("  # macOS / Linux:")
        print('  export SILICONFLOW_API_KEY="sk-你的key"')
        print("")
        print("获取 API Key：https://cloud.siliconflow.cn/account/ak")
        sys.exit(1)

    # --- 读取图片文件 ---
    path = Path(image_path)
    if not path.exists():
        print(f"错误: 文件不存在: {image_path}")
        sys.exit(1)

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        ext_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime_type = ext_map.get(path.suffix.lower(), "image/png")

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # --- 调用 API ---
    from openai import OpenAI

    base_url = os.environ.get(
        "SILICONFLOW_BASE_URL",
        "https://api.siliconflow.cn/v1",
    )
    model = os.environ.get("VISION_MODEL", "Qwen/Qwen3-VL-8B-Instruct")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                {"type": "text", "text": question},
            ],
        }],
        max_tokens=4096,
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
