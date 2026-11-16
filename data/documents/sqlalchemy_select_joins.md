# SQLAlchemy：select、标量结果、JOIN 与分页

> 来源：https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
> 范围：SQLAlchemy 2.0
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 查询结果
select(Model) 构建查询，execute 执行并返回结果包装；scalars 提取每行的第一个元素。选择两个字段时，每行含两项，不能用 scalars 期待得到完整映射。
## JOIN
内连接只保留能匹配的组合；外连接保留指定一侧无匹配的行，对应列可能为 None。一对多连接可能让主表在结果中重复，统计时需明确统计行还是实体。
## 分页
order_by 保证明确排序，offset 跳过前面的行，limit 限制返回数量。稳定分页通常还需要唯一字段作为排序补充。
## 项目示例
select(id, revision) 执行后 result.all() 得到二元行，可转成编号到版本的字典。资料列表 scalars().all() 则返回模型对象。
## 常见误区
select 只是构建表达式，未必已经发 SQL。外连接后在 WHERE 对右表做非空筛选，可能改变原本保留无匹配行的效果。

## 官方来源

[SQLAlchemy：select、标量结果、JOIN 与分页](https://docs.sqlalchemy.org/en/20/tutorial/data_select.html)
