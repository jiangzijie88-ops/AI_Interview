# FastAPI：async def、普通 def 与阻塞调用

> 来源：https://fastapi.tiangolo.com/async/
> 范围：FastAPI 在线文档；以安装版本为准
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 路径函数选择
使用可等待的数据库或 HTTP 客户端时，用 async def 并 await。FastAPI 调用的普通 def 路径函数和同步依赖通常在线程池执行。
## 重要边界
你自己在 async 函数内直接调用的普通工具函数，不会被 FastAPI 自动转移到线程池。同步阻塞网络、文件操作或长计算可能阻塞事件循环。
## 并发与并行
异步主要改善 I/O 等待期间的调度。CPU 密集任务不因为添加 async 就变快，应结合线程、进程或任务系统评估。
## 项目应用
异步数据库查询和模型接口使用 await；FAISS 保存本地文件通过 asyncio.to_thread 执行。对普通返回 None 的 add 或文件保存直接 await 会 TypeError。
## 常见误区
接口全写 async 并不自动正确，也不是每个辅助函数都要 async。应看调用实际是否阻塞以及是否提供异步接口。

## 官方来源

[FastAPI：async def、普通 def 与阻塞调用](https://fastapi.tiangolo.com/async/)
