# LangChain：消息角色、工具消息与历史

> 来源：https://docs.langchain.com/oss/python/langchain/messages
> 范围：LangChain Python 在线文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 消息是什么
聊天模型通常接收消息序列。SystemMessage 提供规则，HumanMessage 表示用户输入，AIMessage 表示模型响应，ToolMessage 表示工具执行结果。消息可能包含文字、结构化内容块及工具调用信息。
## 工具消息
模型请求工具时会给出调用名称、参数与标识。应用执行工具后，通过匹配调用标识的 ToolMessage 返回结果。仅把工具结果写成普通用户消息，可能丢失调用关联。
## 历史管理
一次 invoke 不代表模型自动记住以前的请求；应用需显式传入历史或通过状态与检查点维护历史。上下文长度有限，历史增长时应裁剪或总结，并保持必要的工具消息配对。
## 项目应用
单题点评传入独立题目和回答即可，不必将所有练习历史都塞进消息。来源快照在业务数据库中保存，不等于聊天历史。
## 常见误区
角色区分不能保证模型永远服从规则；仍需验证工具参数、权限和输出。AIMessage 并不保证只有纯文本。

## 官方来源

[LangChain：消息角色、工具消息与历史](https://docs.langchain.com/oss/python/langchain/messages)
