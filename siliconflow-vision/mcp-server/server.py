#!/usr/bin/env python3
"""
SiliconFlow Vision MCP Server

为 Claude 桌面端提供视觉识别能力的 MCP 服务器。
通过调用硅基流动（SiliconFlow）API 实现图片识别、OCR、图表分析等功能。

环境变量:
    SILICONFLOW_API_KEY   你的 SiliconFlow API Key（必填）
                          获取: https://cloud.siliconflow.cn/account/ak

    SILICONFLOW_BASE_URL  API 地址（可选）
                          默认: https://api.siliconflow.cn/v1

    SILICONFLOW_MODEL     默认视觉模型（可选）
                          默认: Qwen/Qwen2.5-VL-32B-Instruct

支持的模型:
    - Qwen/Qwen3-VL-235B-A22B-Instruct  旗舰视觉推理
    - Qwen/Qwen2.5-VL-32B-Instruct      默认（性价最优）
    - Qwen/Qwen2.5-VL-72B-Instruct      大杯
    - Qwen/Qwen2.5-VL-7B-Instruct       最快最便宜
    - glm-4/glm-4.6v                    GLM 视觉模型
    - deepseek-ai/deepseek-vl2          DeepSeek 视觉模型
"""

import base64
import os
import mimetypes
from pathlib import Path
from typing import Optional

from openai import OpenAI
from mcp.server.fastmcp import FastMCP

# --- Configuration ---
DEFAULT_MODEL = "Qwen/Qwen2.5-VL-32B-Instruct"

mcp = FastMCP("siliconflow-vision")


# --- Helpers ---
def _get_base_url() -> str:
    return os.environ.get(
        "SILICONFLOW_BASE_URL",
        "https://api.siliconflow.cn/v1",
    )


def _get_client() -> OpenAI:
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        raise ValueError(
            "SILICONFLOW_API_KEY environment variable is not set. "
            "Get your key at https://cloud.siliconflow.cn/account/ak"
        )
    return OpenAI(api_key=api_key, base_url=_get_base_url())


def _get_model() -> str:
    return os.environ.get("SILICONFLOW_MODEL", DEFAULT_MODEL)


def _encode_image_to_base64(file_path: str) -> tuple[str, str]:
    """Read a local image file and return (base64_data_url, mime_type)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None or not mime_type.startswith("image/"):
        ext_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".svg": "image/svg+xml",
        }
        mime_type = ext_map.get(path.suffix.lower(), "image/png")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{data}", mime_type


# --- MCP Tools ---
@mcp.tool()
def describe_image(
    image_path_or_url: str,
    question: str = "请详细描述这张图片里的内容。如果图片里有文字，请完整识别提取出来。",
    model: Optional[str] = None,
) -> str:
    """
    使用 SiliconFlow 视觉模型识别/描述图片内容。

    Args:
        image_path_or_url: 本地图片文件路径（如 /Users/me/photo.png）或图片 URL
        question:    你想问这张图片的问题（默认：详细描述图片内容并识别其中的文字）
        model:       视觉模型名称（可选，默认 Qwen/Qwen2.5-VL-32B-Instruct）

    Returns:
        模型的文字回复
    """
    client = _get_client()
    chosen_model = model or _get_model()

    if image_path_or_url.startswith(("http://", "https://")):
        image_block = {
            "type": "image_url",
            "image_url": {"url": image_path_or_url},
        }
    else:
        data_url, _ = _encode_image_to_base64(image_path_or_url)
        image_block = {
            "type": "image_url",
            "image_url": {"url": data_url},
        }

    response = client.chat.completions.create(
        model=chosen_model,
        messages=[
            {
                "role": "user",
                "content": [
                    image_block,
                    {"type": "text", "text": question},
                ],
            }
        ],
        max_tokens=4096,
    )

    return response.choices[0].message.content


@mcp.tool()
def ocr_image(
    image_path_or_url: str,
    language: str = "自动检测",
) -> str:
    """
    从图片中提取/识别文字（OCR）。

    Args:
        image_path_or_url: 本地图片文件路径或图片 URL
        language:          期望识别的语言（默认自动检测）

    Returns:
        图片中识别到的文字内容
    """
    prompt = f"请完整提取图片中的所有文字内容。语言偏好：{language}。只输出文字内容，不要加解释。"
    return describe_image(image_path_or_url, question=prompt, model=None)


@mcp.tool()
def answer_question_about_image(
    image_path_or_url: str,
    question: str,
    model: Optional[str] = None,
) -> str:
    """
    针对图片内容回答一个具体问题。适合做图表分析、内容推理等。

    Args:
        image_path_or_url: 本地图片文件路径或图片 URL
        question:          你想针对这张图片问的问题
        model:             视觉模型名称（可选）

    Returns:
        模型的回答
    """
    return describe_image(image_path_or_url, question=question, model=model)


# --- Entry point ---
def main():
    """Entry point for 'siliconflow-vision-mcp' console script."""
    mcp.run()


if __name__ == "__main__":
    mcp.run()
