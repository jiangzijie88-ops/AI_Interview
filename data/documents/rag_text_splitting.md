# RAG：递归文本切分、重叠与片段质量

> 来源：https://reference.langchain.com/python/langchain-text-splitters/character/RecursiveCharacterTextSplitter
> 范围：LangChain Text Splitters 在线 API；包含项目实践归纳
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 为什么切分
完整文章可能含多个主题，以片段检索可以降低无关上下文并更准确找到答案所在段落。短文可不拆，切得越碎并不一定越好。
## 递归切分
RecursiveCharacterTextSplitter 按分隔符顺序尝试；段落过长时继续用较细边界拆分。配置的长度度量决定 chunk_size 是字符、token 或其他单位。
## 重叠
chunk_overlap 用于缓解边界信息丢失，是目标重叠，并非每段必须固定重复相同字符数。代码、表格和解释分离时应人工检查。
## 项目配置
当前按 len 计数，800 字符、100 字符重叠，优先段落/换行/中文标点。英文同字符数可能包含更少词。中文翻译后也应重新预览。
## 质量边界
切分器不理解完整语义。一个片段含太多主题会影响向量表达；过小则丢失定义的前提。阈值与切分质量需一起评估，不能仅看返回数量。

## 官方来源

[RAG：递归文本切分、重叠与片段质量](https://reference.langchain.com/python/langchain-text-splitters/character/RecursiveCharacterTextSplitter)
