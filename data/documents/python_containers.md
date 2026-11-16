# Python：列表、元组、字典、集合与推导式

> 来源：https://docs.python.org/3.11/tutorial/datastructures.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 容器选择
列表是有序可变序列；元组常用于固定结构数据；字典保存键值映射；集合保存不重复元素。字典键与集合元素需要可哈希。
## 常用操作
append 添加一个元素，extend 迭代加入多个元素。列表原地修改方法通常返回 None，不能用 a=a.append(x) 期待得到列表。
字典保持插入顺序，但这不等于按键排序。集合不提供可依赖的插入排序语义。
## 推导式
[item.id for item in items] 创建列表；{item.id for item in items} 创建去重集合；{item.id: item.title for item in items} 创建映射。
## 项目应用
索引包含同一文章的多个片段，使用集合统计文章编号，可避免把片段数误认为文章数。
## 常见误区
[] * n 不会产生 n 个独立空列表。遍历容器同时增删可能导致跳过或报错，优先创建新结果。

## 官方来源

[Python：列表、元组、字典、集合与推导式](https://docs.python.org/3.11/tutorial/datastructures.html)
