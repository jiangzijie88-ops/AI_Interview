# LangGraph：持久化、thread_id 与状态恢复

> 来源：https://docs.langchain.com/oss/python/langgraph/persistence
> 范围：LangGraph Python 持久化文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 核心职责
持久化层保存图运行的检查点，支持后续读取状态、恢复和人工介入等能力。thread_id 用于将调用关联到同一条持久化执行线程，不是操作系统线程编号。
## 状态与存储
checkpointer 负责保存和读取执行状态；thread_id 指定哪条执行线索。内存实现不会在进程结束后保留数据，数据库等持久化实现可以跨进程生命周期保存。
## 业务区别
工作流 checkpoint 保存执行进度；题目快照保存当次出题内容；点评来源快照保存当时参考的片段。三者不是同一份数据。
## 恢复边界
持久化不等于外部数据库操作天然只执行一次。节点恢复或重试仍可能重复副作用，应使用幂等键、唯一约束等机制。
## 项目应用
稳定构造 user/session/answer 对应的 thread_id，使同一道回答的多次请求访问同一图状态。后端仍要核对所有权，知道 thread_id 不代表有权限。

## 官方来源

[LangGraph：持久化、thread_id 与状态恢复](https://docs.langchain.com/oss/python/langgraph/persistence)
