import httpx
import streamlit as st

# 后端地址，集中写在这里，方便以后修改
API_URL = "http://127.0.0.1:8000"

st.title("AI 面试平台")

# Streamlit 交互时会重新运行脚本
# session_state 用来保存当前页面会话中的登录状态
if "token" not in st.session_state:
    st.session_state.token = None


# 没有 token 时，显示登录表单
if st.session_state.token is None:
    with st.form("login_form"):
        username = st.text_input("用户名")

        # type="password"：隐藏输入内容
        password = st.text_input("密码", type="password")

        # 表单内的输入集中在点击此按钮后提交
        submitted = st.form_submit_button("登录")

    if submitted:
        try:
            # 发送登录请求，json 参数会把字典作为 JSON 请求体
            response = httpx.post(
                f"{API_URL}/users/login",
                json={
                    "username": username,
                    "password": password,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                # 你的后端返回字段名是 token
                st.session_state.token = response.json()["token"]

                # 重新运行页面，进入已登录分支
                st.rerun()
            elif response.status_code == 401:
                st.error("用户名或密码错误")
            elif response.status_code == 422:
                st.error("请检查用户名和密码长度")
            else:
                st.error(f"登录失败，状态码：{response.status_code}")

        except httpx.RequestError:
            st.error("无法连接后端，请确认后端已启动")

    # 未登录时，允许展开注册区域
    with st.expander("没有账号？点击注册"):
        with st.form("register_form"):
            # key 用来区分注册和登录表单中的同名输入框
            register_username = st.text_input(
                "用户名",
                max_chars=20,
                key="register_username",
            )

            register_password = st.text_input(
                "密码",
                type="password",
                max_chars=20,
                help="请输入 6～20 个字符",
                key="register_password",
            )

            confirm_password = st.text_input(
                "确认密码",
                type="password",
                max_chars=20,
                key="register_confirm_password",
            )

            register_nickname = st.text_input(
                "昵称",
                max_chars=20,
                key="register_nickname",
            )

            register_submitted = st.form_submit_button("注册")

        # 表单提交后，再检查并发送请求
        if register_submitted:
            username = register_username.strip()

            if not username:
                st.error("用户名不能为空")
            elif not 6 <= len(register_password) <= 20:
                st.error("密码长度应为 6～20 个字符")
            elif register_password != confirm_password:
                st.error("两次输入的密码不一致")
            else:
                try:
                    response = httpx.post(
                        f"{API_URL}/users/register",
                        json={
                            "username": username,
                            "password": register_password,
                            "nickname": register_nickname,
                        },
                        timeout=10.0,
                    )

                    if response.status_code == 201:
                        st.success("注册成功，请在上方登录")
                    elif response.status_code in (400, 409):
                        # 显示后端返回的业务错误，例如用户名已存在
                        st.error(response.json()["detail"])
                    elif response.status_code == 422:
                        st.error("输入不符合要求，请检查后重试")
                    else:
                        st.error(
                            f"注册失败，状态码：{response.status_code}"
                        )

                except httpx.RequestError:
                    st.error("无法连接后端，请确认后端已启动")


# 已有 token 时，显示用户信息和退出按钮
else:
    st.success("已保存登录凭证")

    if st.button("查看我的信息"):
        try:
            # 在请求头中携带 token，让后端识别当前用户
            response = httpx.get(
                f"{API_URL}/users/me",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                user = response.json()
                st.write("用户名：", user["username"])
                st.write("昵称：", user["nickname"])
            elif response.status_code == 401:
                # token 已过期或无效，清除后重新显示登录表单
                st.session_state.token = None
                st.rerun()
            else:
                st.error(f"获取用户信息失败：{response.status_code}")

        except httpx.RequestError:
            st.error("无法连接后端，请稍后重试")

    # 已登录用户可以修改自己的昵称
    with st.form("nickname_form"):
        new_nickname = st.text_input(
            "新昵称",
            max_chars=20,
            help="留空可以清空昵称",
        )
        nickname_submitted = st.form_submit_button("保存昵称")

    if nickname_submitted:
        try:
            # 携带 token，提交新昵称
            response = httpx.patch(
                f"{API_URL}/users/me",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}",
                },
                json={"nickname": new_nickname},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                st.success(data["message"])
                st.write("当前昵称：", data["nickname"])
            elif response.status_code == 401:
                # 登录凭证失效，返回登录页面
                st.session_state.token = None
                st.rerun()
            elif response.status_code == 422:
                st.error("昵称不能超过 20 个字符")
            else:
                st.error(f"修改失败，状态码：{response.status_code}")

        except httpx.RequestError:
            st.error("无法连接后端，请稍后重试")

    if st.button("退出登录"):
        # 清除当前页面保存的 token
        st.session_state.token = None
        st.rerun()