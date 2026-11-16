from langchain_core.documents import Document
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.knowledge_documents import KnowledgeDocument
from backend.services.document_splitter import split_document

import asyncio
from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.llm import get_embedding_model
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "runtime" / "knowledge_index"
INDEX_CONFIG_PATH = INDEX_DIR / "config.json"



async def collect_index_documents(db: AsyncSession) -> list[Document]:
    """读取已审核资料，转换为带来源信息的文本片段。"""

    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.status == "approved")
        .order_by(KnowledgeDocument.id)
    )
    documents = result.scalars().all()

    index_documents = []

    for document in documents:
        # 一篇完整资料会产生一个或多个片段
        chunks = split_document(document.content)

        for position, chunk in enumerate(chunks, start=1):
            index_documents.append(
                Document(
                    # 真正用于后续向量化的片段正文
                    page_content=chunk,

                    # 来源信息，用于展示引用和检查版本
                    metadata={
                        "document_id": document.id,
                        "revision": document.revision,
                        "position": position,
                        "title": document.title,
                        "source_url": document.source_url or "",
                        "version_note": document.version_note or "",
                    },
                )
            )

    return index_documents




async def rebuild_document_index(db: AsyncSession) -> dict:
    """读取全部已审核资料，重新建立本地向量索引。"""

    # 复用上一步：获取带来源信息的资料片段
    documents = await collect_index_documents(db)

    if not documents:
        raise ValueError("没有可建立索引的已审核资料")

    embedding_model = get_embedding_model()

    # 内部调用 Embedding API，将片段转换为向量并创建索引
    vector_store = await FAISS.afrom_documents(
        documents,
        embedding_model,
    )

    # 本地文件写入是同步操作，放到线程中执行
    await asyncio.to_thread(
        vector_store.save_local,
        str(INDEX_DIR),
    )

    # 记录本次索引使用的模型，以及实际生成的向量维度
    index_config = {
        "embedding_model": embedding_model.model,
        "dimension": vector_store.index.d,
    }

    await asyncio.to_thread(
        INDEX_CONFIG_PATH.write_text,
        json.dumps(index_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 统计参与建立索引的原始资料数量
    document_ids = {
        document.metadata["document_id"]
        for document in documents
    }

    return {
        "document_count": len(document_ids),
        "chunk_count": len(documents),
        "message": "资料索引已建立",
    }



async def search_documents(
    db: AsyncSession,
    query: str,
    k: int = 3,
    max_distance: float = 1.2,
) -> list[Document]:
    """检索相关片段，只返回仍然审核通过且版本一致的资料。"""

    query = query.strip()
    if not query:
        raise ValueError("检索问题不能为空")

    # 必须先成功建立索引
    if not (
        (INDEX_DIR / "index.faiss").exists()
        and (INDEX_DIR / "index.pkl").exists()
    ):
        raise ValueError("资料索引不存在，请先重建索引")

    embedding_model = get_embedding_model()

    if not INDEX_CONFIG_PATH.is_file():
        raise ValueError("索引缺少模型配置，请重新建立索引")

    config_text = await asyncio.to_thread(
        INDEX_CONFIG_PATH.read_text,
        encoding="utf-8",
    )
    index_config = json.loads(config_text)

    if index_config.get("embedding_model") != embedding_model.model:
        raise ValueError("Embedding 模型已变化，请重新建立索引")

    # 只读取本项目自己生成、可信的本地索引
    vector_store = await asyncio.to_thread(
        FAISS.load_local,
        str(INDEX_DIR),
        embedding_model,
        allow_dangerous_deserialization=True,
    )

    if index_config.get("dimension") != vector_store.index.d:
        raise ValueError("索引维度与保存的配置不一致，请重新建立索引")

    # 当前资料量较小，先取出按相似度排序的全部候选，
    # 再过滤已停用或已修改的旧片段
    candidates = await vector_store.asimilarity_search_with_score(
        query,
        k=vector_store.index.ntotal,
    )

    # 重新查询当前审核通过的资料及其最新修订号
    result = await db.execute(
        select(KnowledgeDocument.id, KnowledgeDocument.revision)
        .where(KnowledgeDocument.status == "approved")
    )
    current_revisions = dict(result.all())

    valid_documents = []

    for document, distance in candidates:
        # 距离过大的片段不作为参考资料返回
        if float(distance) > max_distance:
            continue
        document_id = document.metadata["document_id"]
        indexed_revision = document.metadata["revision"]

        # 当前状态有效，并且资料版本与索引版本一致
        if current_revisions.get(document_id) == indexed_revision:
            # 创建新的 metadata 字典，附上本次查询的距离
            document.metadata = {
                **document.metadata,
                "distance": float(distance),
            }
            valid_documents.append(document)

            if len(valid_documents) >= k:
                break

    return valid_documents







