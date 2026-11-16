# Python：迭代器、生成器与 yield

> 来源：https://docs.python.org/3.11/tutorial/classes.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 可迭代对象与迭代器
可迭代对象能产生迭代器；迭代器通过 next 逐项提供值，耗尽时抛出 StopIteration。列表可以反复取得新的迭代器，一个已耗尽的生成器不会自动重置。
## 生成器
含 yield 的函数返回生成器，执行到 yield 暂停，下一次迭代从暂停处继续。生成器可按需生产数据，减少一次性构造列表，但不保证其引用的所有数据都不占内存。
## 与 return 区别
return 结束函数，yield 暂停并产出值。yield from 可委托子迭代过程。
## 项目应用
FastAPI 的 yield 依赖借助框架管理资源进入与退出，不能把它理解成“自动提交事务”。清理与提交规则仍取决于依赖代码。
## 常见误区
生成器不是 LangGraph interrupt。Python 生成器的局部续行机制与图恢复时重跑节点是不同机制，不要互相套用。

## 官方来源

[Python：迭代器、生成器与 yield](https://docs.python.org/3.11/tutorial/classes.html)
