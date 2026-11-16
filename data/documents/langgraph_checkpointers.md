# LangGraph：检查点后端选择与生命周期

> 来源：https://docs.langchain.com/oss/python/langgraph/checkpointers
> 范围：LangGraph Python Checkpointers 文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 保存器与业务数据库
checkpointer 实现检查点的写入、读取与相关序列化。它可以使用内存或持久化后端，选择要结合本地学习、并发规模与部署方式。
## 生命周期
数据库型保存器通常需要连接或上下文管理器，应在应用生命周期内创建、复用并关闭。不要每个节点各自创建互不关联的保存器，否则恢复配置容易混乱。
## 本地与生产
内存适合快速试验；SQLite 适合轻量本地场景。生产选型需要考虑并发、连接管理、备份和部署，不应仅把本地文件复制到多实例就认为数据共享。
## 项目应用
FastAPI lifespan 打开 AsyncSqliteSaver，再构建图，服务退出时关闭。MySQL 保存业务记录，SQLite 保存图检查点，两个存储没有自动组成统一事务。
## 常见误区
保存器不替代用户授权。重启能读到状态，不等于所有节点副作用都实现了恰好一次。

## 官方来源

[LangGraph：检查点后端选择与生命周期](https://docs.langchain.com/oss/python/langgraph/checkpointers)
