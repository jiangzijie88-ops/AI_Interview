from pydantic import BaseModel, Field

# 定义注册接口接受的数据，以及各字段的校验规则
class UserCreate(BaseModel):
    username: str = Field( min_length=1, max_length=20, description="用户名")
    password: str = Field( min_length=6, max_length=20, description="密码")
    nickname: str = Field( default="", max_length=20, description="昵称")


# 登录只需要用户名和密码，不需要nickname
class UserLogin(BaseModel):
    username: str = Field( min_length=1, max_length=20, description="用户名")
    password: str = Field( min_length=6, max_length=20, description="密码")


# 修改昵称时，只接收 nickname 字段
class UserNicknameUpdate(BaseModel):
    # 允许空字符串，表示清空昵称；最多 20 个字符
    nickname: str = Field(max_length=20)




