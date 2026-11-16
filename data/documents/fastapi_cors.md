# FastAPI：CORS、源与浏览器请求

> 来源：https://fastapi.tiangolo.com/tutorial/cors/
> 范围：FastAPI CORS 教程
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 源的定义
源由协议、主机、端口组成。即使同一主机，不同端口也属于不同源。浏览器跨源请求可能执行预检并要求服务端允许相关来源、方法和请求头。
## 配置
CORSMiddleware 可设置允许来源等规则。使用凭证时应明确列出可信来源，不要认为通配符适用于所有认证方式。
## 边界
CORS 是浏览器策略，不是身份认证或防止所有客户端访问的机制。curl、服务器端 HTTP 客户端通常不受浏览器 CORS 限制。
## 项目应用
Streamlit Python 端用 httpx 请求 FastAPI，属于服务器间调用，不能遇到所有连接错误都归因于 CORS。以后换成浏览器 JavaScript 直接调用 API，再检查跨源配置。
## 自测问题
localhost:8501 与 localhost:8000 是否同源？允许跨域是否意味着允许任何用户修改资料？

## 官方来源

[FastAPI：CORS、源与浏览器请求](https://fastapi.tiangolo.com/tutorial/cors/)
