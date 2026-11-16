# SQLAlchemy：Session、flush、commit 与 rollback

> 来源：https://docs.sqlalchemy.org/en/20/orm/session_basics.html
> 范围：SQLAlchemy 2.0
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## Session 的职责
Session 管理一组 ORM 对象、身份映射及事务工作，不是用户登录会话，也不是一条面试练习。它可能按需取得数据库连接。
## 常用操作
add 把对象加入工作单元；flush 将待处理变化发送到数据库事务；commit 提交事务，通常会先 flush；rollback 回滚未提交事务。flush 不等于最终提交。
## 对象跟踪
由当前 Session 查询的对象通常受到跟踪，修改属性后可在提交时产生更新，不必再次 add。身份映射不是跨请求的通用结果缓存。
## 异常
flush 失败后要显式 rollback 或退出相应事务上下文，才能按正确状态继续使用会话。关闭会话不应被理解为自动提交成功业务。
## 项目应用
点评先提交 processing，再调用模型，最后提交 succeeded/failed；两个提交是两个事务，不是一个跨网络调用的原子事务。
## 面试要求
明确提交边界，区分对象内存修改、发送 SQL 与事务提交。

## 官方来源

[SQLAlchemy：Session、flush、commit 与 rollback](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
