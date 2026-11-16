# Python：参数、默认值与可变默认参数

> 来源：https://docs.python.org/3.11/tutorial/controlflow.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 参数传递
位置参数按位置绑定，关键字参数按名称绑定。默认值让调用方可省略参数；定义与调用时应注意必填参数的位置。
## 可变默认值
默认参数表达式在函数定义时计算，不是每次调用重新计算。用列表或字典作为默认值，修改后可能被后续调用共享。
## 自写示例
def collect(item, result=None): 内部在 result is None 时创建新列表，再追加 item。这样可区分“调用方没有提供容器”和“明确提供空容器”。
## 工程应用
generate_feedback 的 retrieved_context 使用字符串默认值，可以兼容旧调用；不能把每次请求不同的来源列表写成默认 [] 后不断追加。
## 常见误区
默认 None 不等于禁止传 None，需按业务校验。*args 收集额外位置参数，**kwargs 收集额外关键字参数，不是自动验证任意参数的 schema。
## 核心要求
知道默认值创建时机，比死记“列表不能作默认值”更重要。

## 官方来源

[Python：参数、默认值与可变默认参数](https://docs.python.org/3.11/tutorial/controlflow.html)
