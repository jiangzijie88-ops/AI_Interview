from ui import page_heading, difficulty_label, status_label
import httpx
import streamlit as st
import json


# 显示题目管理区域，由 app.py 调用
def show_question_admin(api_url, token):
    page_heading("题库管理", "维护题目内容与状态，审核后用于组题。")

    try:
        # 先读取选项，供筛选、新增和编辑表单共同使用
        job_response = httpx.get(
            f"{api_url}/job_roles", timeout=10.0
        )
        point_response = httpx.get(
            f"{api_url}/knowledge_points", timeout=10.0
        )

        # 非成功响应抛出异常，避免继续解析错误数据
        job_response.raise_for_status()
        point_response.raise_for_status()

        # 建立“编号 → 名称”的对应关系
        jobs = {
            item["id"]: item["name"]
            for item in job_response.json()
        }
        points = {
            item["id"]: item["name"]
            for item in point_response.json()
        }
    except httpx.HTTPError:
        st.error("岗位或知识点加载失败")
        return

    section = st.radio("题库工作区", ["浏览与维护", "新增题目", "批量导入"], horizontal=True, key="question_admin_section")
    if section == "新增题目":
        _show_question_create(api_url, token, jobs, points)
    elif section == "批量导入":
        show_question_import(api_url, token)
    else:
        action = st.radio("维护操作", ["题目列表", "详情与审核", "编辑题目"], horizontal=True, key="question_admin_action")
        if action == "题目列表":
            _show_question_list(api_url, token, jobs, points)
        elif action == "编辑题目":
            show_question_editor(api_url, token, jobs, points)
        else:
            _show_question_detail(api_url, token, jobs, points)
            with st.expander("审核与停用"):
                _show_question_status(api_url, token, jobs, points)

def _show_question_list(api_url, token, jobs, points):
    # 表单提交时，再统一查询
    with st.form("question_list_form"):
        difficulty_col, status_col, job_col, point_col, page_col = st.columns([1, 1, 2, 2, 1])
        difficulty = difficulty_col.selectbox(
            "难度", ["全部", "basic", "advanced"], format_func=difficulty_label
        )
        status = status_col.selectbox(
            "状态", ["全部", "draft", "approved", "disabled"], format_func=status_label
        )

        # None 表示“全部”，其他选项是数据库中的岗位 ID
        filter_job_id = job_col.selectbox(
            "筛选岗位",
            options=[None] + list(jobs),
            format_func=lambda item_id: (
                "全部" if item_id is None else jobs[item_id]
            ),
        )

        filter_point_id = point_col.selectbox(
            "筛选知识点",
            options=[None] + list(points),
            format_func=lambda item_id: (
                "全部" if item_id is None else points[item_id]
            ),
        )

        page = page_col.number_input("页码", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("查询题目")

    if submitted:
        # 查询参数，对应后端接口中的 page、page_size 等
        params = {"page": page, "page_size": 10}

        # 选择“全部”时，不发送相应筛选条件
        if difficulty != "全部":
            params["difficulty"] = difficulty

        # 选择“全部”时，不发送该筛选条件
        if filter_job_id is not None:
            params["job_role_id"] = filter_job_id

        if filter_point_id is not None:
            params["knowledge_point_id"] = filter_point_id

        if status != "全部":
            params["status"] = status

        try:
            response = httpx.get(
                f"{api_url}/questions",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                st.write("符合条件的题目数量：", data["total"])

                if data["items"]:
                    # 将后端返回的字典列表显示成表格
                    rows = [{"编号": item["id"], "题目": item["content"],
                             "难度": difficulty_label(item["difficulty"]),
                             "状态": status_label(item["status"]), "修订号": item["revision"]}
                            for item in data["items"]]
                    st.dataframe(rows, hide_index=True, width="stretch")
                else:
                    st.info("当前页没有题目")

            elif response.status_code == 401:
                st.session_state.token = None
                st.rerun()
            elif response.status_code == 403:
                st.error("需要管理员权限")
            else:
                st.error(f"查询失败，状态码：{response.status_code}")

        except httpx.RequestError:
            st.error("无法连接后端，请稍后重试")
        # 分隔题目列表和详情区域


def _show_question_detail(api_url, token, jobs, points):
    st.write("查看题目详情")

    with st.form("question_detail_form"):
        # 输入列表中实际存在的题目编号
        question_id = st.number_input(
            "题目 ID",
            min_value=1,
            value=1,
            step=1,
        )
        detail_submitted = st.form_submit_button("查看详情")

    if detail_submitted:
        try:
            # 把题目 ID 放进路径，调用已有的详情接口
            response = httpx.get(
                f"{api_url}/questions/{question_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                question = response.json()

                # 用 write 展示纯文本，避免把题目里的代码当作 Markdown
                st.write("题目：", question["content"])
                st.write("难度：", difficulty_label(question["difficulty"]))
                st.write("状态：", status_label(question["status"]))
                st.write("修订号：", question["revision"])

                st.write("参考要点：", question["reference_points"])
                st.write("常见错误：", question["common_mistakes"] or "未填写")
                st.write("追问方向：", question["followup_direction"] or "未填写")
                st.write("参考来源：", question["sources"] or "未填写")

                # 从关联列表中取出名称，拼成易读的文字
                job_names = [
                    job["name"] for job in question["job_roles"]
                ]
                point_names = [
                    point["name"] for point in question["knowledge_points"]
                ]

                st.write("适用岗位：", "、".join(job_names))
                st.write("知识点：", "、".join(point_names))

            elif response.status_code == 404:
                st.warning("这道题不存在，请检查题目 ID")
            elif response.status_code == 401:
                st.session_state.token = None
                st.rerun()
            elif response.status_code == 403:
                st.error("需要管理员权限")
            else:
                st.error(f"查询失败，状态码：{response.status_code}")

        except httpx.RequestError:
            st.error("无法连接后端，请稍后重试")


def _show_question_status(api_url, token, jobs, points):
    st.write("审核与停用")

    # 页面显示中文，提交给后端时转换为约定的英文值
    status_options = {
        "审核通过": "approved",
        "停用": "disabled",
        "退回草稿": "draft",
    }

    with st.form("question_status_form"):
        status_question_id = st.number_input(
            "要操作的题目 ID",
            min_value=1,
            value=1,
            step=1,
            key="status_question_id",
        )

        target_status = st.selectbox(
            "目标状态",
            list(status_options.keys()),
        )

        # 审核需要管理员先阅读题目内容
        confirmed = st.checkbox("我已查看题目详情，确认执行此操作")
        status_submitted = st.form_submit_button("保存状态")

    if status_submitted:
        if not confirmed:
            st.warning("请先查看题目详情，并勾选确认")
        else:
            try:
                response = httpx.patch(
                    f"{api_url}/questions/{status_question_id}/status",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"status": status_options[target_status]},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success(
                        f"题目 {data['id']} 状态已更新为：{target_status}"
                    )
                    st.info("请重新查询列表或详情，查看最新状态")
                elif response.status_code == 404:
                    st.warning("题目不存在，请检查 ID")
                elif response.status_code == 401:
                    st.session_state.token = None
                    st.rerun()
                elif response.status_code == 403:
                    st.error("需要管理员权限")
                else:
                    st.error(f"操作失败，状态码：{response.status_code}")

            except httpx.RequestError:
                st.error("无法连接后端，请稍后重试")


def _show_question_create(api_url, token, jobs, points):
    st.write("新增题目")

    if not jobs or not points:
        st.info("请先准备岗位和知识点数据")
        return

    with st.form("question_create_form"):
        # 多行文本输入，长度与当前后端规则一致
        new_content = st.text_area("问题正文", max_chars=1000)
        new_reference = st.text_area("参考要点", max_chars=1000)

        new_difficulty = st.selectbox(
            "题目难度", ["basic", "advanced"], format_func=difficulty_label
        )

        # 实际选择的是 ID，页面通过 format_func 显示名称
        new_job_ids = st.multiselect(
            "适用岗位",
            options=list(jobs),
            format_func=lambda item_id: jobs[item_id],
        )
        new_point_ids = st.multiselect(
            "考查知识点",
            options=list(points),
            format_func=lambda item_id: points[item_id],
        )

        new_mistakes = st.text_area("常见错误（可选）", max_chars=1000)
        new_followup = st.text_area("追问方向（可选）", max_chars=1000)
        new_sources = st.text_area("参考来源（可选）", max_chars=1000)

        create_submitted = st.form_submit_button("保存为草稿")

    if create_submitted:
        if not new_content.strip() or not new_reference.strip():
            st.warning("请填写问题正文和参考要点")
        elif not new_job_ids or not new_point_ids:
            st.warning("请至少选择一个岗位和一个知识点")
        else:
            try:
                response = httpx.post(
                    f"{api_url}/questions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "content": new_content,
                        "reference_points": new_reference,
                        "difficulty": new_difficulty,
                        "job_role_ids": new_job_ids,
                        "knowledge_point_ids": new_point_ids,
                        "common_mistakes": new_mistakes.strip() or None,
                        "followup_direction": new_followup.strip() or None,
                        "sources": new_sources.strip() or None,
                    },
                    timeout=10.0,
                )

                if response.status_code == 201:
                    data = response.json()
                    st.success(f"草稿已保存，题目 ID：{data['id']}")
                    st.info("请重新查询列表；确认内容后再审核")
                elif response.status_code == 401:
                    st.session_state.token = None
                    st.rerun()
                elif response.status_code == 403:
                    st.error("需要管理员权限")
                elif response.status_code in (400, 422):
                    st.error("保存失败，请检查填写内容和所选编号")
                else:
                    st.error(f"保存失败，状态码：{response.status_code}")

            except httpx.RequestError:
                st.error("无法连接后端，请稍后重试")




def show_question_editor(api_url, token, jobs, points):
    st.subheader("编辑题目")

    # 放在表单外，切换 ID 后重新加载对应题目
    question_id = st.number_input(
        "要编辑的题目 ID",
        min_value=1,
        value=1,
        step=1,
        key="edit_question_id",
    )

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = httpx.get(
            f"{api_url}/questions/{question_id}",
            headers=headers,
            timeout=10.0,
        )

        if response.status_code == 401:
            st.session_state.token = None
            st.rerun()
        elif response.status_code == 403:
            st.error("需要管理员权限")
            return
        elif response.status_code == 404:
            st.warning("题目不存在")
            return

        response.raise_for_status()
        question = response.json()
    except httpx.HTTPError:
        st.error("加载题目失败，请检查后端连接")
        return

    # 不同题目使用不同表单标识，避免复用上一道题的输入
    with st.form(f"edit_question_form_{question_id}"):
        content = st.text_area(
            "问题正文", value=question["content"], max_chars=1000
        )
        reference = st.text_area(
            "参考要点", value=question["reference_points"], max_chars=1000
        )

        difficulties = ["basic", "advanced"]
        difficulty = st.selectbox(
            "难度",
            difficulties,
            index=difficulties.index(question["difficulty"]),
        )

        job_ids = st.multiselect(
            "岗位",
            options=list(jobs),
            default=[job["id"] for job in question["job_roles"]],
            format_func=lambda item_id: jobs[item_id],
        )
        point_ids = st.multiselect(
            "知识点",
            options=list(points),
            default=[point["id"] for point in question["knowledge_points"]],
            format_func=lambda item_id: points[item_id],
        )

        mistakes = st.text_area(
            "常见错误",
            value=question["common_mistakes"] or "",
            max_chars=1000,
        )
        followup = st.text_area(
            "追问方向",
            value=question["followup_direction"] or "",
            max_chars=1000,
        )
        sources = st.text_area(
            "参考来源",
            value=question["sources"] or "",
            max_chars=1000,
        )

        st.caption("保存后题目会回到草稿状态，需要重新审核。")
        submitted = st.form_submit_button("保存修改")

    if submitted:
        if not content.strip() or not reference.strip():
            st.warning("正文和参考要点不能为空")
        elif not job_ids or not point_ids:
            st.warning("请至少选择一个岗位和一个知识点")
        else:
            try:
                response = httpx.put(
                    f"{api_url}/questions/{question_id}",
                    headers=headers,
                    json={
                        "content": content,
                        "reference_points": reference,
                        "difficulty": difficulty,
                        "job_role_ids": job_ids,
                        "knowledge_point_ids": point_ids,
                        "common_mistakes": mistakes.strip() or None,
                        "followup_direction": followup.strip() or None,
                        "sources": sources.strip() or None,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    st.success("修改成功，题目已回到草稿状态")
                    st.info("请重新查询详情确认修改结果")
                elif response.status_code == 401:
                    st.session_state.token = None
                    st.rerun()
                elif response.status_code == 403:
                    st.error("需要管理员权限")
                elif response.status_code == 404:
                    st.warning("题目不存在")
                elif response.status_code in (400, 422):
                    st.error("输入不符合要求，请检查内容和关联选项")
                else:
                    st.error(f"保存失败，状态码：{response.status_code}")

            except httpx.RequestError:
                st.error("无法连接后端，请稍后重试")



def show_question_import(api_url, token):
    st.subheader("批量导入题目")

    # 接收用户选择的文件，不会自动调用后端
    uploaded_file = st.file_uploader(
        "选择题目 JSON 文件",
        type=["json"],
        key="question_import_file",
    )

    if uploaded_file is None:
        return

    try:
        # utf-8-sig 同时兼容普通 UTF-8 和带 BOM 的 UTF-8 文件
        text = uploaded_file.getvalue().decode("utf-8-sig")
        items = json.loads(text)
    except UnicodeDecodeError:
        st.error("请使用 UTF-8 编码保存 JSON 文件")
        return
    except json.JSONDecodeError as exc:
        st.error(f"JSON 格式错误：第 {exc.lineno} 行，{exc.msg}")
        return

    # 后端要求最外层是列表，一次接收 1～100 道题
    if not isinstance(items, list):
        st.error("文件最外层必须是列表，也就是用 [] 包住多道题")
        return

    if not 1 <= len(items) <= 100:
        st.error("一次只能导入 1～100 道题")
        return

    st.write("文件中的题目数量：", len(items))
    st.caption("导入后保存为草稿；重复导入会重复新增题目。")

    # 只有点击按钮时才发送写入请求
    if st.button("开始导入", key="start_question_import"):
        try:
            with st.spinner("正在导入，请等待结果……"):
                response = httpx.post(
                    f"{api_url}/questions/import",
                    headers={"Authorization": f"Bearer {token}"},
                    json=items,
                    timeout=60.0,
                )

            if response.status_code == 200:
                result = response.json()

                st.write(
                    f"共 {result['total']} 道，"
                    f"成功 {result['success_count']} 道，"
                    f"失败 {result['failed_count']} 道"
                )

                # 每一项对应文件中的一道题
                for item in result["results"]:
                    if item["success"]:
                        st.write(
                            f"第 {item['index']} 道：成功，"
                            f"题目 ID 为 {item['id']}"
                        )
                    else:
                        st.error(f"第 {item['index']} 道：失败")

                        if "errors" in item:
                            # 字段校验错误：显示字段和原因
                            for error in item["errors"]:
                                st.write(
                                    f"{error['field']}：{error['message']}"
                                )
                        else:
                            # 业务或数据库操作错误
                            st.write(item["error"])

                st.info("请重新查询题目列表，检查导入的草稿")

            elif response.status_code == 401:
                st.session_state.token = None
                st.rerun()
            elif response.status_code == 403:
                st.error("需要管理员权限")
            elif response.status_code == 422:
                st.error("提交的数据不符合批量接口要求")
            else:
                st.error(
                    "未拿到完整导入结果，"
                    "可能已有部分题目保存，请先查询列表再决定是否重试。"
                )

        except httpx.RequestError:
            # 客户端断开不代表后端没有写入
            st.error(
                "连接失败或等待超时，无法确认最终导入结果。"
                "请先查询题目列表，不要立即重复导入。"
            )





