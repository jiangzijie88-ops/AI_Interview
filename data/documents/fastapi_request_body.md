# FastAPI：路径参数、查询参数与请求体

> 来源：https://fastapi.tiangolo.com/tutorial/body/
> 范围：FastAPI 与 Pydantic 请求体
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 三种来源
URL 路径中的参数用于定位资源，查询字符串常用于筛选分页，请求体承载结构化数据。Pydantic 模型可声明 JSON 请求结构。
## 校验
类型、默认值、Field 或 Query 约束共同参与校验。参数是否必填由声明方式决定，类型可为 None 与是否必填不是完全同一件事。
## 示例
PUT /knowledge_documents/3 中 3 定位资料；GET 列表的 page=2 控制分页；JSON 中的 title/content 是编辑内容。
## 工程应用
创建 schema 与更新 schema 可不同。完整 PUT 和部分 PATCH 的语义应明确，不能把省略字段一律解释为不修改。
## 常见误区
前端发送 JSON 应使用正确请求头与编码。GET 请求体缺乏广泛通用支持，通常把检索条件放查询参数。校验通过不等于引用的资料编号存在，也不等于调用者有权限。
## 自测问题
schema 校验和数据库存在性检查分别在哪发生？

## 官方来源

[FastAPI：路径参数、查询参数与请求体](https://fastapi.tiangolo.com/tutorial/body/)
