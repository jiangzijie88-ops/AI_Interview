# Python：异常传播、else、finally 与异常链

> 来源：https://docs.python.org/3.11/tutorial/errors.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 基本流程
try 包裹可能出错的代码；except 捕获匹配异常；else 在 try 正常结束时执行；finally 用于无论结果如何都需要执行的清理。
## 传播与定位
未捕获异常沿调用栈传播，traceback 从外层调用展示到出错位置。定位时先关注末尾异常类型和自己代码中的行，而不是逐行修改第三方库。
## 捕获边界
优先捕获明确异常。except Exception 可以作为业务层边界，但应记录并定义降级策略，不应把程序错误一概静默忽略。raise 可继续抛出原异常；raise NewError from exc 可保留原因链。
## 项目应用
内层捕获资料检索异常，继续无资料点评；外层捕获模型生成异常，标记点评失败。保存数据库的错误还需要事务清理。
## 常见误区
finally 中 return 可能掩盖原异常。异常对象中的字符串可能包含敏感数据，日志不应无条件打印密钥或完整用户内容。

## 官方来源

[Python：异常传播、else、finally 与异常链](https://docs.python.org/3.11/tutorial/errors.html)
