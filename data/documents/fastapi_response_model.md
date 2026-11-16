# FastAPI：响应模型、字段过滤与接口契约

> 来源：https://fastapi.tiangolo.com/tutorial/response-model/
> 范围：FastAPI 与 Pydantic 响应模型
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 响应模型职责
response_model 或合适的返回类型声明定义接口输出结构，参与文档、验证与字段过滤。接口内部对象可能有更多字段，但对外只应暴露允许字段。
## 安全意义
用户 ORM 对象可能包含 password_hash，不能因为数据库查到了就全部返回。输出 schema 应与输入、数据库模型分开。
## 项目边界
将 retrieval_status 等字段写入点评 JSON 后，接口若后来增加严格响应 schema，需要把这些字段纳入定义，否则可能被过滤。普通字典直接返回与声明响应模型的行为不同。
## 失败处理
服务端返回不符合响应契约的数据通常是后端实现问题，不应假装是用户请求校验错误。
## 常见误区
response_model 不负责自动授权；字段过滤也不能修复此前日志泄露。模型字段描述是文档，不等于任意复杂业务约束都已强制执行。

## 官方来源

[FastAPI：响应模型、字段过滤与接口契约](https://fastapi.tiangolo.com/tutorial/response-model/)
