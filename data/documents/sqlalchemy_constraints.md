# SQLAlchemy：主键、外键、唯一约束与关联表

> 来源：https://docs.sqlalchemy.org/en/20/core/constraints.html
> 范围：SQLAlchemy 2.0
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 各种约束
主键唯一标识行；外键声明当前表某列引用目标表的候选键；唯一约束限制列或列组合不能出现重复业务键；非空约束拒绝 NULL。
## 关系方向
question_id 配置 ForeignKey('questions.id') 表示当前表的 question_id 引用 questions 表的 id，不是反过来。
## 多对多
题目与岗位通过关联表保存多对多关系，可用两列组合主键避免同一对关系重复。单列可在多行出现，组合不可重复。
## 业务应用
回答表对 question_record_id 设置唯一约束，约束每份练习题目快照最多一条主回答；引用的是快照主键而非公共题号。
## 边界
ORM 模型改了不代表现有数据库表自动迁移。外键和唯一约束不替代权限检查，删除级联行为也必须明确设置而非想当然。

## 官方来源

[SQLAlchemy：主键、外键、唯一约束与关联表](https://docs.sqlalchemy.org/en/20/core/constraints.html)
