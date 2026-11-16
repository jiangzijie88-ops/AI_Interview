# SQLAlchemy：AsyncSession、会话工厂与并发

> 来源：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
> 范围：SQLAlchemy 2.0
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 创建关系
create_async_engine 创建异步引擎；async_sessionmaker 配置会话工厂；每次工厂调用产生 AsyncSession。引擎管理连接资源，Session 组织当前工作。
## 调用
execute、commit、rollback 等异步 I/O 操作用 await。add 是登记对象，通常不需要 await。不能仅因对象是 AsyncSession 就给所有方法加 await。
## 并发边界
AsyncSession 是有状态事务对象，不应被多个并发任务共享。各独立任务应有自己的会话，避免事务和对象状态相互干扰。
## 对象加载
异步 ORM 应注意过期属性或懒加载触发的隐式 I/O。expire_on_commit=False 可减少提交后读取属性时意外重新加载，但不等于数据永远最新。
## 项目应用
检索与保存点评分开使用会话，避免检索数据库异常影响原保存事务。会话退出与模型请求成功是不同事件。

## 官方来源

[SQLAlchemy：AsyncSession、会话工厂与并发](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
