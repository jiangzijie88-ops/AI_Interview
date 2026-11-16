# LangGraph：部分状态更新与 Reducer

> 来源：https://docs.langchain.com/oss/python/langgraph/graph-api-state
> 范围：LangGraph Python 状态定义文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 更新规则
节点返回状态的部分更新。未返回的字段保持现有值；未配置 reducer 的字段通常采用新值覆盖。Reducer 定义一个字段如何合并原值与新值。
## 列表字段
列表不会自动追加。若通过 Annotated 为列表设置追加型 reducer，更新可以合并；未设置时，新列表替换旧列表。消息字段的专用 reducer 还可根据消息 ID 更新已有消息。
## 并行场景
多个节点在同一步更新同一字段时，应明确合并语义；不能假定某个写入必然获胜。Reducer 的设计应避免依赖不可保证的执行顺序。
## 示例
原状态为 stage=loading、answer_id=4；节点只返回 stage=main_feedback，则 answer_id 仍为 4。追加型列表返回空列表通常不表示清空已有内容。
## 常见误区
TypedDict 声明结构不自动执行运行时校验。Reducer 只处理状态字段合并，不替你提交数据库事务。

## 官方来源

[LangGraph：部分状态更新与 Reducer](https://docs.langchain.com/oss/python/langgraph/graph-api-state)
