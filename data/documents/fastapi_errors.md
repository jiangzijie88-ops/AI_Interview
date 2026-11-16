# FastAPI：HTTPException、422 与业务错误

> 来源：https://fastapi.tiangolo.com/tutorial/handling-errors/
> 范围：FastAPI 错误处理
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 异常返回
raise HTTPException 可以中止当前处理并返回对应状态码及 detail。它是抛异常，不是返回一个 HTTPException 对象。
## 分层理解
请求字段格式不符通常由校验层返回 422；资源不存在可返回 404；没有有效身份与权限不足应区分处理；业务冲突可选择 409。
## 工程策略
业务服务产生可解释错误，接口映射为 HTTP 响应。内部异常应记录便于排查，但面向用户的提示不应暴露连接串、密钥或完整堆栈。
## 项目应用
索引不存在时检索接口显示可操作提示；主点评业务捕获该失败后选择无资料继续点评，二者处理策略不同。
## 常见误区
前端超时不代表服务端没有完成写入。返回 200 也不代表所有子任务成功，例如批量导入可在响应中分别报告各项结果。

## 官方来源

[FastAPI：HTTPException、422 与业务错误](https://fastapi.tiangolo.com/tutorial/handling-errors/)
