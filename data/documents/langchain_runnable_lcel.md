# LangChain：Runnable、LCEL 与异步链

> 来源：https://reference.langchain.com/python/langchain-core/runnables/base/RunnableSequence
> 范围：LangChain Core 在线 API
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 核心概念
Runnable 是具有统一调用接口的可执行组件。RunnableSequence 将组件按顺序连接，前一步输出成为下一步输入。竖线运算符 | 常用于组装序列，并不是启动任务的符号。组装时不等于已经调用模型。
## 常用调用
invoke 进行同步单次调用，ainvoke 是异步调用；batch、abatch 接收一批输入；stream、astream 用于流式消费。组件支持哪些输出与流式行为，要看其实现。
提示词模板可以接收字典并生成模型消息，因此提示词也能成为链的一环。模型接收这些消息，输出对象再交给解析或后处理。
## 项目示例
feedback_prompt | structured_model 表示“格式化消息，再请求结构化模型”。await chain.ainvoke({...}) 才执行整条链。不能写 await chain.invoke(...)：invoke 返回的最终对象通常不可等待。
## 常见误区
普通同步函数不会因为位于异步业务中就自动成为非阻塞操作。批量调用也不保证无限并发，应遵守提供方限流。
## 自测问题
链在哪里组装、在哪里执行？前后组件传递的是什么？

## 官方来源

[LangChain：Runnable、LCEL 与异步链](https://reference.langchain.com/python/langchain-core/runnables/base/RunnableSequence)
