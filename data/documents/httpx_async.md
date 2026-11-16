# HTTPX：AsyncClient、连接复用与响应清理

> 来源：https://www.python-httpx.org/async/
> 范围：HTTPX 官方异步文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 同步与异步
Client 适合同步调用，AsyncClient 用于 asyncio 等异步环境。异步请求写 await client.get(...)，不能以为把同步 httpx.get 放进 async 函数就自动非阻塞。
## 生命周期
async with AsyncClient() 管理连接释放。需要复用连接时，可在合理的应用生命周期内复用客户端，避免热点循环每次重新创建。
## 流式响应
流式读取应使用正确的上下文或主动关闭响应，防止连接资源泄露。读取和关闭方法要区分同步、异步版本。
## 项目区别
Streamlit 脚本中的同步 httpx 调用与 FastAPI 异步路径函数环境不同，不能机械要求所有前端 Python 调用都变成 async。
## 工程边界
超时表示客户端等待失败，不等于远端操作回滚。写请求重试应配合幂等机制，避免一次超时导致多次新增。

## 官方来源

[HTTPX：AsyncClient、连接复用与响应清理](https://www.python-httpx.org/async/)
