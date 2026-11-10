import asyncio
from sqlalchemy import select
from backend.database import AsyncSessionLocal, async_engine
from backend.models.users import User



async def main():
    # 输入已经注册的用户名，不需要输入密码
    username = input("请输入要设为管理员的用户名：").strip()

    if not username:
        print("用户名不能为空")
        return

    try:
        # 创建本次命令使用的数据库会话
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if user is None:
                print("账号不存在，请先通过注册页面创建")
                return

            if user.role == "admin":
                print("该账号已经是管理员")
                return

            # 修改角色并保存
            user.role = "admin"
            await db.commit()

            print(f"已将 {user.username} 设置为管理员")
    finally:
        # 命令结束时释放连接池，即使中途退出也会执行
        await async_engine.dispose()


# 只有直接运行此模块时，才执行初始化命令
if __name__ == "__main__":
    asyncio.run(main())