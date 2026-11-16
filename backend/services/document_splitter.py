from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_document(content: str) -> list[str]:
    """将一篇资料的正文切分为多个文本片段。"""

    # 空白正文不产生片段
    if not content.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        # 优先按段落切分，再尝试换行、中文标点、空格
        separators=["\n\n", "\n", "。", "；", " ", ""],
        # 尽量保留原来的首尾空白，减少对代码缩进的影响
        strip_whitespace=False,
    )

    chunks = splitter.split_text(content)

    # 排除只包含空白的片段，保留其他片段的原始内容
    return [chunk for chunk in chunks if chunk.strip()]