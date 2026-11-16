# FastAPI：密码哈希、JWT 与 Bearer 身份验证

> 来源：https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
> 范围：FastAPI 安全教程；认证协议与项目实现需区分
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 登录与凭证
后端验证用户名与密码后，可以签发包含用户标识、过期时间等声明的 JWT。密码应使用适当密码哈希算法保存，验证时比较哈希，不保存明文密码。
## JWT 与密钥
JWT 签名用于发现篡改，不代表载荷被加密。密钥保存在服务端，用来签发或验证，不能发给前端。验证需要限制允许的算法并检查过期等必需声明。
## Bearer
Authorization: Bearer token 表示请求携带持有者凭证。拿到有效 token 的人可能以对应身份发请求，因此应避免泄露。
## 授权
身份通过不等于可访问所有资源。用户只能读取自己的回答、管理员才能管理公共资料，应在数据库查询和业务依赖中核对。
## 边界
退出页面并不自动撤销所有已经签发的 token；即时撤销需要另行设计。本项目登录 JSON 接口不应直接等同教程完整 OAuth2 表单流程。

## 官方来源

[FastAPI：密码哈希、JWT 与 Bearer 身份验证](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
