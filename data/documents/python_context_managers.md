# Python：with、async with 与资源清理

> 来源：https://docs.python.org/3.11/library/contextlib.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 上下文管理
with 将资源进入与退出绑定到代码块。上下文管理器提供 __enter__、__exit__；异步对应 __aenter__、__aexit__，通过 async with 使用。
## contextlib
contextmanager 可用包含一次 yield 的生成器定义上下文管理器；asynccontextmanager 用异步生成器定义异步管理器。yield 前准备资源，之后执行退出逻辑，通常借助 try/finally 确保清理。
## 异常传播
块内异常会进入退出逻辑；如果管理器只清理资源，应让异常继续传播，不能误把业务失败变成成功。
## 项目应用
async with AsyncSessionLocal() as db 创建并在退出时关闭会话。是否提交不能仅由 async with 推断；应看是否使用事务上下文或显式 commit。
## 常见误区
with 不只用于文件，async with 也不代表自动并发。清理能关闭连接，但不会撤销已经提交的外部副作用。

## 官方来源

[Python：with、async with 与资源清理](https://docs.python.org/3.11/library/contextlib.html)
