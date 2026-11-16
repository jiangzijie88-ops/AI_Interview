# LangChain：结构化输出与结果校验

> 来源：https://docs.langchain.com/oss/python/langchain/structured-output
> 范围：LangChain Python 在线文档；Agent 与直接模型接口需区分
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 目标
结构化输出让应用获得字段明确的结果，而不是自行从自然语言中猜字段。schema 可使用 Pydantic 等形式定义。Agent 文档区分提供方原生结构化方式与基于工具调用的方式。
## 直接模型调用
本项目使用 model.with_structured_output(FeedbackContent, method='function_calling')，再与提示词连接；这是直接模型调用，不能把 Agent 的返回字段机械套用过来。
## 两层正确性
解析成功表示结果符合相关结构约束，不表示事实正确。Pydantic 字段描述不能自动强制所有业务规则，提示词中的“最多三条”也不等于 Field 的硬约束。
## 应用建议
对引用编号、题号范围、字段间关系做业务校验；失败与用户答案分开保存，允许重试点评而不重复提交答案。
## 常见误区
输出 JSON 不代表已验证 JSON；有效 JSON 也可能字段不符。重试有成本，并且不一定修复事实错误。

## 官方来源

[LangChain：结构化输出与结果校验](https://docs.langchain.com/oss/python/langchain/structured-output)
