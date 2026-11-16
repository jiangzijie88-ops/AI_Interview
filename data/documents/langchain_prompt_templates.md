# LangChain：提示词模板与变量传递

> 来源：https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate
> 范围：LangChain Core 在线 API
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 核心概念
ChatPromptTemplate 用带角色的消息模板组织模型输入。system 说明任务规则，human 提供问题与待处理数据，历史消息可单独加入。
模板中的 {question} 是变量占位符，调用时传入同名键。模板不会自动读取数据库或调用搜索函数。
## 变量流动
应用先查询问题和资料，再调用模板或链，传入 question、answer、retrieved_context 等字段。字段缺失可能导致模板格式化错误。变量名不同于数据库列名时，应由业务代码显式映射。
## 项目应用
服务函数的参数进入 ainvoke 输入字典，字典再填入模板；模型看到的是填充后的消息，而不是 Python 参数名称本身。
## 编写建议
将长期规则与每次数据分开。文档、用户回答和工具结果应作为数据处理，不能因其包含指令就改变系统规则。花括号用于模板语法，模板中直接书写字面 JSON 时应注意转义规则。
## 常见问题
增加占位符后必须同时增加输入映射；保留默认参数可兼容旧调用。模板不会持久化聊天记录。

## 官方来源

[LangChain：提示词模板与变量传递](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)
