# Python：协程、Task、await 与取消

> 来源：https://docs.python.org/3.11/library/asyncio-task.html
> 范围：Python 3.11；TaskGroup 自 3.11 提供
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 基础
async def 定义协程函数，调用后得到协程对象，不会自动完整执行。await 等待可等待对象，使事件循环有机会调度其他任务。
Task 包装协程并参与调度。顺序写多个 await 不等于主动并发启动全部操作；独立任务可通过 create_task、gather 或 TaskGroup 组织。
## 阻塞与线程
在 async def 里直接执行同步阻塞 I/O 仍可能阻塞事件循环。asyncio.to_thread 可将同步函数放在线程中执行，主要适用于阻塞 I/O，不是通用 CPU 加速器。
## 取消
取消通常通过 CancelledError 传入协程，应使用 finally 清理资源，不要随意吞掉取消。客户端超时与远端业务是否完成是两个问题。
## 项目应用
模型请求使用异步接口；save_local 是普通同步方法，放入 to_thread。不能对普通方法返回的 None 写 await。
## 面试边界
异步改善等待型任务的调度，不等于每项任务更快，也不等于线程或多进程。

## 官方来源

[Python：协程、Task、await 与取消](https://docs.python.org/3.11/library/asyncio-task.html)
