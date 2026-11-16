# Python：类型注解、TypedDict、Literal 与 NotRequired

> 来源：https://docs.python.org/3.11/library/typing.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 注解与执行
Python 普通类型注解主要帮助工具检查和阅读，运行时不会仅因写了 int 就自动拒绝字符串。Pydantic 等库会利用类型声明另行校验。
## 类型表达
str | None 表示值可以是字符串或 None。list[str] 表示字符串列表。Literal 限定预期字面值，TypedDict 描述字典键值结构，NotRequired 表示这个键可以缺失。
## 易混点
键可缺失与值可为 None 不同：NotRequired[int] 不要求键存在；int | None 允许键值为 None，但是否必须有键由结构声明决定。
## 项目应用
LangGraph 状态中必须的 user_id 与可选 followup_id 可分别声明。stage 的 Literal 描述允许的阶段名称，但不会自动触发图路由。
## 自测问题
类型注解能否阻止直接调用函数时传错类型？TypedDict 是不是数据库模型？

## 官方来源

[Python：类型注解、TypedDict、Literal 与 NotRequired](https://docs.python.org/3.11/library/typing.html)
