import httpx
import streamlit as st

from question_admin import show_question_admin
from interview import show_interview_create, show_interview_list

# 后端地址，集中写在这里，方便以后修改
API_URL = "http://127.0.0.1:8000"

st.title("AI 面试平台")

# Streamlit 交互时会重新运行脚本
# session_state 用来保存当前页面会话中的登录状态
if "token" not in st.session_state:
    st.session_state.token = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


def clear_login():
    """退出时同时清理页面、用户信息和练习草稿，避免下个账号沿用。"""
    st.session_state.clear()
    st.session_state.token = None
    st.session_state.current_page = "home"


# 没有 token 时，显示登录表单
if st.session_state.token is None:
    # 登录过期后重新登录，也从练习首页进入
    st.session_state.current_page = "home"
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


# 已登录时，通过页面状态在练习首页和我的主页之间切换
else:
    # 首页只保留个人主页入口，账号操作集中放在个人主页
    _, navigation = st.columns([3, 1])
    with navigation:
        if st.session_state.current_page == "home":
            if st.button("我的主页", use_container_width=True):
                st.session_state.current_page = "profile"
                st.rerun()
        else:
            if st.button("返回首页", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    current_user = None

    # 复用现有接口：个人主页显示资料，首页判断管理员权限
    try:
        response = httpx.get(
            f"{API_URL}/users/me",
            headers=headers,
            timeout=10.0,
        )

        if response.status_code == 200:
            current_user = response.json()
        elif response.status_code == 401:
            clear_login()
            st.rerun()
        else:
            st.error(f"读取用户身份失败：{response.status_code}")
    except httpx.RequestError:
        st.error("无法连接后端，请稍后重试")

    if st.session_state.current_page == "profile":
        st.subheader("我的主页")

        notice = st.session_state.pop("profile_notice", None)
        if notice:
            st.success(notice)

        if current_user is not None:
            # 进入个人主页就读取并显示信息，无需再点击查询按钮
            st.write("用户名：", current_user["username"])
            st.write("昵称：", current_user["nickname"] or "未设置")

            with st.form("nickname_form"):
                new_nickname = st.text_input(
                    "新昵称",
                    value=current_user["nickname"] or "",
                    max_chars=20,
                    help="留空可以清空昵称",
                )
                nickname_submitted = st.form_submit_button("保存昵称")

            if nickname_submitted:
                try:
                    response = httpx.patch(
                        f"{API_URL}/users/me",
                        headers=headers,
                        json={"nickname": new_nickname},
                        timeout=10.0,
                    )

                    if response.status_code == 200:
                        # 重跑后重新读取个人信息，让顶部昵称同步更新
                        st.session_state.profile_notice = response.json()["message"]
                        st.rerun()
                    elif response.status_code == 401:
                        clear_login()
                        st.rerun()
                    elif response.status_code == 422:
                        st.error("昵称不能超过 20 个字符")
                    else:
                        st.error(f"修改失败，状态码：{response.status_code}")
                except httpx.RequestError:
                    st.error("无法连接后端，请稍后重试")

        st.divider()
        # 后端暂时不可连接时，也允许清除本机登录状态
        if st.button("退出登录"):
            clear_login()
            st.rerun()

    else:
        # 练习首页只显示练习功能，以及管理员的题库区域
        st.divider()
        show_interview_create(API_URL, st.session_state.token)

        st.divider()
        show_interview_list(API_URL, st.session_state.token)

        if current_user is not None and current_user["role"] == "admin":
            show_question_admin(API_URL, st.session_state.token)
