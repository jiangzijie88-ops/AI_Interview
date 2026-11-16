# FastAPI：yield 依赖与数据库会话清理

> 来源：https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/
> 范围：FastAPI 在线文档；退出时机与 scope 随版本核对
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 生命周期
yield 之前准备资源，yield 把资源交给路径函数，之后进行退出处理。FastAPI 使用类似上下文管理器的方式管理这些依赖。
## 数据库示例
async with AsyncSessionLocal() as session 创建会话，yield session 提供给接口。异常路径可 rollback 并重新抛出，退出时关闭会话。
## 事务边界
yield 不会自动 commit。由依赖统一提交还是业务服务显式提交，是应用设计决定，必须查看实际代码。项目目前由接口或 manager 明确提交。
## 异常原则
捕获业务异常只做清理后应重新抛出，避免框架认为请求成功。不要在异常后继续使用失效事务。
## 版本注意
依赖的清理时间与流式响应、scope 参数等有关，不能把某个旧版本行为当成永久规则。对 BackgroundTasks 等后台操作应使用自身管理的资源，而非依赖已经退出的请求会话。

## 官方来源

[FastAPI：yield 依赖与数据库会话清理](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
