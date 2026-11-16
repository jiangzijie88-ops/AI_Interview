import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# 明确读取项目根目录的 .env ，不依赖其他文件先加载配置
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")



def get_chat_model():
  """创建用于 AI点评 的模型客户端"""
  return ChatOpenAI(
    # 通义千问的调用凭证
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 请求实际发送到阿里云，而不是 OpenAI
    base_url=os.getenv("LLM_BASE_URL"),
    # 使用.env 中指定的模型
    model=os.getenv("LLM_MODEL"),
    # 单次请求等待实践上限，单位秒
    timeout=60,
    # 暂不自动重试，后续由点评业务明确处理失败
    max_retries=0,
  )



def get_embedding_model():
  """创建用于资料和问题向量化的客户端。"""

  return OpenAIEmbeddings(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("EMBEDDING_MODEL"),
    # 直接发送原始文本，由阿里云处理文本长度
    check_embedding_ctx_length=False,
    # 先每次提交一条文本，保持调用简单
    chunk_size=1,
    request_timeout=60,
    max_retries=0,
  )









