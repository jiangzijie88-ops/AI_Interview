# RAG：FAISS 本地保存、距离与来源映射

> 来源：https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/vectorstores/faiss.py
> 范围：LangChain Community FAISS 集成源码
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 基本流程
FAISS 包装器把向量搜索与文本存储、ID 映射结合。from_documents 或异步版本利用 Embedding 客户端创建索引；检索时将查询向量与索引比较并还原片段。
## 距离
默认 L2 索引返回的分值越小越近。不要当成概率或要求范围为 0～1。其他距离策略或归一化方式变化后，阈值含义也会改变。
## 保存与加载
save_local 保存 FAISS 数据及文本映射。load_local 恢复，需使用匹配的 Embedding 客户端。pkl 涉及反序列化，只加载自己生成且可信的文件。
## 项目实践
先按相似度找候选，再核对资料审核状态与 revision。保留正文、标题、来源和版本，才能展示引用和排除旧片段。
## 常见误区
top-k 只保证最多取若干相近候选，不证明相关。增加文件锁、原子版本切换与配置校验属于应用责任，不是 save_local 自动保证。

## 官方来源

[RAG：FAISS 本地保存、距离与来源映射](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/vectorstores/faiss.py)
