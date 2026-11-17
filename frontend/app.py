import os
import httpx
import streamlit as st

from ui import setup_page, page_heading
from question_admin import show_question_admin
from document_admin import show_document_admin
from interview import show_interview_create, show_interview_list, show_current_interview

setup_page()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
st.session_state.setdefault("token", None)
st.session_state.setdefault("current_page", "home")


def clear_login():
    """退出后清理身份、导航和所有练习草稿。"""
    st.session_state.clear()
    st.session_state.token = None
    st.session_state.current_page = "home"


if st.session_state.token is None:
    st.session_state.current_page = "home"
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        page_heading("AI 面试平台", "按知识点练习，在回答中发现进步。")
        auth_mode = st.radio("账号入口", ["登录", "注册"], horizontal=True, label_visibility="collapsed")
        if auth_mode == "登录":
            with st.form("login_form"):
                username = st.text_input("用户名")

                # type="password"：隐藏输入内容
                password = st.text_input("密码", type="password")

                # 表单内的输入集中在点击此按钮后提交
                submitted = st.form_submit_button("登录", type="primary", width="stretch")

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

        else:
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

                    register_submitted = st.form_submit_button("注册", type="primary", width="stretch")

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


else:
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

    # 每轮读取服务端身份，管理入口不信任客户端保存的角色。
    with st.sidebar:
        st.markdown('<div class="brand-mark"><strong>AI 面试练习</strong><p>从回答，到真正理解。</p></div>', unsafe_allow_html=True)
        if current_user is not None:
            st.caption(current_user.get("nickname") or current_user["username"])
        st.caption("练习工作台")
        pages = [("开始练习", "home"), ("我的练习", "sessions"), ("我的主页", "profile")]
        if current_user is not None and current_user["role"] == "admin":
            pages += [("题库管理", "questions"), ("资料管理", "documents")]
        for label, name in pages:
            if name == "questions":
                st.divider()
                st.caption("管理中心")
            active = st.session_state.current_page == name or (
                name == "sessions" and st.session_state.current_page == "practice"
            )
            if st.button(label, key=f"nav_{name}", width="stretch",
                         type="primary" if active else "secondary"):
                st.session_state.current_page = name
                st.rerun()
        st.divider()
        st.caption("账号设置与退出登录位于「我的主页」。")

    page = st.session_state.current_page
    if page == "profile":
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

    elif current_user is None:
        st.info("暂时无法读取身份，请稍后刷新，或进入我的主页退出登录。")
    elif page == "questions":
        if current_user["role"] == "admin":
            show_question_admin(API_URL, st.session_state.token)
        else:
            st.warning("需要管理员权限。")
    elif page == "documents":
        if current_user["role"] == "admin":
            show_document_admin(API_URL, st.session_state.token)
        else:
            st.warning("需要管理员权限。")
    elif page == "sessions":
        show_interview_list(API_URL, st.session_state.token)
    elif page == "practice":
        if st.button("← 返回我的练习"):
            st.session_state.current_page = "sessions"
            st.rerun()
        session_id = st.session_state.get("active_session_id")
        if session_id is not None:
            show_current_interview(API_URL, st.session_state.token, session_id)
        else:
            st.info("请从我的练习中选择记录。")
    else:
        show_interview_create(API_URL, st.session_state.token)
