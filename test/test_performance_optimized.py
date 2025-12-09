from google import genai
import os # 导入 os 库，以使用环境变量
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")

# 请替换为你的 API Key 或从环境变量中获取
client = genai.Client(api_key=GOOGLE_API_KEY)

prompt = "请用一个富有创意的比喻来形容你作为人工智能的感受。"

print(f"**用户输入：** {prompt}\n" + "---")
print("**Gemma 正在回复（流式）：**")

# 关键修正：使用 generate_content_stream 方法
response_stream = client.models.generate_content_stream(
    model=GOOGLE_MODEL,
    contents=prompt
    # 注意：这里不需要再加 stream=True 参数了，因为方法名本身就代表流式调用
)

# 迭代生成器，并逐块打印输出
for chunk in response_stream:
    # chunk.text 包含模型生成的文本块
    # 使用 if chunk.text: 避免打印空块（有时模型会返回只包含元数据的空块）
    if chunk.text:
        print(chunk.text, end="", flush=True)

# 确保最后有一个换行符
print()