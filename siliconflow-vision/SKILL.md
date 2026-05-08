# SiliconFlow Vision

通过调用硅基流动（SiliconFlow）视觉 API 识别图片内容。支持单张图片识别和批量处理截图。

---

## 技能行为概述

当用户说出以下触发语时，你应该自动执行对应操作：
- 「帮我看看这张图 / 这张图片」→ 识别用户提供的图片
- 「这张图里写了什么 / 有什么文字」→ OCR 提取文字
- 「分析最新 N 张截图 / 最近 N 张图」→ 批量识别最近的截图

> 首次使用时，你需要主动引导用户完成一次性的配置。**不要让用户自己去看文档设环境变量**，你直接在对话中询问并帮他们搞定。

---

## 阶段一：首次使用 → 配置向导

用户第一次说「帮我看看这张图」时，不要直接报错，而是启动下面的配置流程。

### 步骤 1：安装 Python 依赖

检查 `openai` 和 `Pillow` 是否已安装。如未安装，执行：

```bash
pip install openai Pillow --break-system-packages
```

执行后告诉用户：「已安装所需依赖 ~」

### 步骤 2：获取 API Key（交互式）

检查记忆中是否已有 `SILICONFLOW_API_KEY`。如果没有，直接在对话中询问用户：

> 「首次使用需要配置一下 SiliconFlow 的 API Key，很简单！
>  1. 打开这个链接注册/登录：https://cloud.siliconflow.cn
>  2. 进入 API Key 管理页面：https://cloud.siliconflow.cn/account/ak
>  3. 点击「新建 API Key」，复制那个以 sk- 开头的密钥
>  4. 粘贴给我就行 ~」

用户粘贴后，立即保存到记忆，并告知用户已保存，以后不用再填。

### 步骤 3：确认截图/图片文件夹路径（交互式）

检查记忆中是否已有 `TARGET_IMAGE_DIR`。如果没有，直接在对话中询问用户：

> 「你的截图或图片存放在哪个文件夹？
>  比如常见的路径有：
>  - Windows：`C:\Users\你的用户名\Pictures\Screenshots`
>  - macOS：`/Users/你的用户名/Pictures/Screenshots`
>  你直接把文件夹路径发给我就行 ~」

用户回复后，将 Windows 路径转换为 Cowork Linux 环境下的对应路径（例如 `C:\Users\xxx` → `/mnt/c/Users/xxx`），然后保存到记忆。

### 步骤 4：创建 vision.py 脚本

在 outputs 目录下创建 `vision.py`（通过 Write 工具写入 `cli/vision.py` 的源码内容），将路径保存到记忆中供后续使用。

### 步骤 5：确认配置完成

告诉用户：「配置完成！现在你可以直接跟我说『帮我看看这张图』或者『最新 3 张截图里有什么』来使用了 ~」

---

## 阶段二：正常使用

### 单张图片识别

当用户提供一张图片（上传或在对话中引用）时：

1. 将用户图片复制到临时路径 `/tmp/vision_input.png`
2. 如果图片尺寸过大，用 Pillow 缩放到约 800px 宽
3. 执行：`python3 <VISION_SCRIPT_DIR>/vision.py /tmp/vision_input.png "[用户的问题]"`

### 批量识别最近截图

当用户说「最新 N 张截图」时：

1. 从记忆中读取 `TARGET_IMAGE_DIR`
2. 执行以下命令，将每张图的识别结果汇总返回：

```bash
ls -t "$TARGET_IMAGE_DIR"/*.png "$TARGET_IMAGE_DIR"/*.jpg 2>/dev/null | head -N | while read f; do
    echo "=== $(basename "$f") ==="