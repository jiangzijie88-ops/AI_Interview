# MySQL：SELECT FOR UPDATE 与并发写入

> 来源：https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html
> 范围：MySQL 8.4 InnoDB
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 锁定读
SELECT ... FOR UPDATE 在事务中读取并锁定相关记录，常用于读取后更新，减少其他事务同时修改带来的冲突。锁范围受索引、查询条件和隔离级别影响，不能简单认为只锁返回的那一行。
## 生命周期
相关锁通常持续到事务提交或回滚。若等待远端模型时一直持锁，可能导致长时间阻塞。应明确哪些状态必须在锁内判断。
## 项目应用
创建点评前核对记录并保存 processing，然后提交释放锁，再执行模型调用。后续请求发现 processing 可返回冲突提示。
## 边界
锁不等于防止所有重复写入。不存在记录时的并发插入需要结合索引和唯一约束设计；进程内 asyncio.Lock 也不能协调多个进程。
## 常见误区
普通 SELECT 与 FOR UPDATE 读方式不同。SKIP LOCKED 跳过锁记录的语义不适用于所有一致性查询。

## 官方来源

[MySQL：SELECT FOR UPDATE 与并发写入](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)
