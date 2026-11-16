# Python：模块、包、import 与 python -m

> 来源：https://docs.python.org/3.11/tutorial/modules.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 模块与包
模块通常对应一个 Python 文件；包组织模块命名空间。import 查找模块并执行其顶层定义，通常在同一进程缓存模块对象。
## 入口
直接运行模块时 __name__ 为 __main__。将临时调用放在 if __name__ == '__main__' 中，可避免其他文件导入时执行测试请求。
## python -m
python -m package.module 让当前解释器按模块路径查找并执行入口，有助于使用正确环境及包上下文。模块路径用点号，不是文件路径斜杠，也不带 .py。
## 项目应用
在项目根目录运行 python -m uvicorn backend.main:app --reload。backend.main 是模块，冒号后 app 是模块中的应用对象。main 拼成 mian 或目录拼成 back 都会导入失败。
## 常见误区
pip 安装到其他解释器不等于当前环境可用。文件名拼错时，增加 __init__.py 不一定能解决根因。

## 官方来源

[Python：模块、包、import 与 python -m](https://docs.python.org/3.11/tutorial/modules.html)
