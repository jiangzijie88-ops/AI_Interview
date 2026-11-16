# Pydantic：模型校验、字段约束与转换

> 来源：https://pydantic.dev/docs/validation/latest/concepts/validators/
> 范围：Pydantic v2 风格
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 模型职责
BaseModel 根据字段类型、约束和校验器处理输入。字段 validator 可在指定阶段清理或检查数据；model validator 可处理跨字段规则。
## 前后校验
before 可处理尚未按目标字段类型解析的输入，after 常用于检查解析后的值。应选择合适模式，不要无意绕过类型校验。
## 项目示例
标题先 strip 再判断空；正文只通过 strip 判断是否全空白，返回原值保留缩进。抛 ValueError 表达输入不符合要求。
## 序列化
model_dump 得到 Python 数据结构，model_dump_json 得到 JSON 文本。model_dump 不一定把任意类型都自动变成 JSON 可编码值，需结合模式与字段类型。
## 常见误区
Field 的 description 是说明，不是任意业务规则的执行器。必填、允许 None 和有默认值需要分别理解。Pydantic model 不是数据库表，也不会自动保存记录。

## 官方来源

[Pydantic：模型校验、字段约束与转换](https://pydantic.dev/docs/validation/latest/concepts/validators/)
