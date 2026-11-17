from ui import difficulty_label, page_heading, practice_intro
import httpx
import streamlit as st
from uuid import uuid4  # 生成每次提交的唯一编号


def show_interview_create(api_url, token):
    practice_intro()
    st.subheader("今天，练习什么？")
    st.caption("先选岗位与难度，再确定本次练习的范围。")

    # 读取岗位和知识点，作为页面选项
    try:
        job_response = httpx.get(
            f"{api_url}/job_roles", timeout=10.0
        )
        point_response = httpx.get(
            f"{api_url}/knowledge_points", timeout=10.0
        )
        job_response.raise_for_status()
        point_response.raise_for_status()

        jobs = {
            item["id"]: item["name"]
            for item in job_response.json()
        }
        points = {
            item["id"]: item["name"]
            for item in point_response.json()
        }
    except httpx.HTTPError:
        st.error("无法加载岗位或知识点")
        return

    if not jobs:
        st.info("暂无可选岗位")
        return

    with st.form("interview_create_form"):
        st.markdown("#### 练习设置")
        job_column, difficulty_column, count_column = st.columns([2, 1, 1])
        job_id = job_column.selectbox(
            "岗位",
            options=list(jobs),
            format_func=lambda item_id: jobs[item_id],
        )

        difficulty = difficulty_column.selectbox(
            "练习难度", ["basic", "advanced"], format_func=difficulty_label
        )

        # index=1：默认选中第二项，也就是 5 道
        question_count = count_column.selectbox(
            "主问题数量", [3, 5, 10], index=1
        )

        point_ids = st.multiselect(
            "知识点",
            options=list(points),
            format_func=lambda item_id: points[item_id],
            help="不选表示不限；选多个时，题目匹配其中任意一个即可",
        )

        st.caption("不选知识点表示不限范围。历史回答与点评可在「我的练习」回看。")
        submitted = st.form_submit_button("创建练习", type="primary", width="stretch")

    if submitted:
        try:
            with st.spinner("正在匹配题目并创建练习……"):
                response = httpx.post(
                    f"{api_url}/interview_sessions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "job_role_id": job_id,
                        "difficulty": difficulty,
                        "question_count": question_count,
                        "knowledge_point_ids": point_ids,
                    },
                    timeout=20.0,
                )

            if response.status_code == 201:
                data = response.json()

                st.session_state.active_session_id = data["id"]
                st.session_state.current_page = "practice"
                st.rerun()

            elif response.status_code == 400:
                # 当前后端的题量不足信息放在 detail 字典中
                detail = response.json()["detail"]
                st.warning(
                    f"{detail['message']}，"
                    f"当前可用 {detail['available_count']} 道，"
                    "请减少题数或调整条件。"
                )

            elif response.status_code == 401:
                st.session_state.token = None
                st.rerun()

            elif response.status_code in (404, 422):
                st.error("配置无效，请刷新页面后重新选择")

            else:
                st.error(
                    "未获取到创建结果，请先查询练习列表，"
                    "确认是否已经创建成功。"
                )

        except httpx.RequestError:
            st.error(
                "连接失败或等待超时，无法确认创建结果。"
                "请先查询练习列表，避免重复创建。"
            )



def show_interview_list(api_url, token):
    page_heading("我的练习", "继续未完成的练习，或回看回答、点评与总结报告。")
    # 提示显示一次后移除，避免以后每次操作都重复出现
    notice = st.session_state.pop("interview_notice", None)
    if notice is not None:
        st.success(notice)

    status_options = {
        "全部": None,
        "进行中": "in_progress",
        "已完成": "completed",
        "提前结束": "ended_early",
    }

    # 放在表单外，切换条件后页面会重新运行并查询
    filter_column, page_column = st.columns([3, 1])
    selected_status = filter_column.selectbox(
        "练习状态",
        options=list(status_options),
        key="interview_list_status",
    )
    page = page_column.number_input(
        "练习列表页码",
        min_value=1,
        value=1,
        step=1,
        key="interview_list_page",
    )

    params = {"page": page, "page_size": 10}

    if status_options[selected_status] is not None:
        params["status"] = status_options[selected_status]

    try:
        response = httpx.get(
            f"{api_url}/interview_sessions",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10.0,
        )

        if response.status_code == 401:
            st.session_state.token = None
            st.rerun()
        elif response.status_code != 200:
            st.error(f"查询练习失败：{response.status_code}")
            return

        data = response.json()
    except httpx.RequestError:
        st.error("无法连接后端，请稍后重试")
        return

    st.write("符合条件的练习数量：", data["total"])

    if not data["items"]:
        st.info("当前页没有练习记录")
        return

    # 转换列名和状态，方便用户阅读
    status_names = {
        "in_progress": "进行中",
        "completed": "已完成",
        "ended_early": "提前结束",
    }

    rows = []

    for session in data["items"]:
        rows.append({
            "练习编号": session["id"],
            "岗位": session["job_role_name"],
            "难度": difficulty_label(session["difficulty"]),
            "主问题数量": session["question_count"],
            "状态": status_names[session["status"]],
            "开始时间（UTC）": session["started_at"],
        })

    st.dataframe(rows, hide_index=True, width="stretch")

    # 所有状态均可打开；结束的练习仅查看历史题目和回答
    sessions = {
        session["id"]: session
        for session in data["items"]
    }

    # None 表示还没有选择，避免自动打开第一条记录
    selected_id = st.selectbox(
        "选择要查看或继续的练习",
        options=[None] + list(sessions),
        format_func=lambda session_id: (
            "请选择"
            if session_id is None
            else (
                f"练习 {session_id} · {sessions[session_id]['job_role_name']}"
                f" · {status_names[sessions[session_id]['status']]}"
            )
        ),
        key="continue_interview_id",
    )

    if st.button("打开练习", type="primary", disabled=selected_id is None):
        st.session_state.active_session_id = selected_id
        st.session_state.current_page = "practice"
        st.rerun()


def save_answer_draft(widget_key, draft_key):
    # 控件切换后可能被 Streamlit 清理，另存一份草稿用于切回来恢复
    st.session_state[draft_key] = st.session_state[widget_key]


def show_current_interview(api_url, token, session_id):
    page_heading(f"练习 #{session_id}", "点击题号自由切换，提交后查看 AI 点评。")
    position_key = f"interview_position_{session_id}"
    if position_key not in st.session_state:
        st.session_state[position_key] = 1

    try:
        response = httpx.get(
            f"{api_url}/interview_sessions/{session_id}/current",
            headers={"Authorization": f"Bearer {token}"},
            params={"position": st.session_state[position_key]},
            timeout=10.0,
        )
    except httpx.RequestError:
        st.error("无法连接后端，请稍后重试")
        return
    if response.status_code == 401:
        st.session_state.token = None
        st.rerun()
    if response.status_code != 200:
        st.error(f"读取练习失败：{response.status_code}")
        return
    data = response.json()
    read_only = data["status"] != "in_progress"
    if read_only:
        status_name = "已完成" if data["status"] == "completed" else "提前结束"
        st.info(f"本次练习{status_name}，可以点击题号查看历史回答。")

        with st.expander("查看练习总结报告"):
            show_interview_report(api_url, token, session_id)
        st.divider()

    # 每个题号旁标注作答状态，切换只改变页面选择，不修改数据库
    st.write(f"已回答 {data['answered_count']} / {data['question_count']} 道")
    st.progress(data["answered_count"] / max(data["question_count"], 1))
    # 每行最多五个题号，十道题也不会挤成一排。
    columns = st.columns(min(len(data["questions"]), 5))
    for index, item in enumerate(data["questions"]):
        column = columns[index % len(columns)]
        label = f"{item['position']} {'已答' if item['answered'] else '未答'}"
        if column.button(
            label,
            key=f"question_{session_id}_{item['id']}",
            type="primary" if item["position"] == data["selected_position"] else "secondary",
        ):
            st.session_state[position_key] = item["position"]
            st.rerun()

    question = data["current_question"]
    st.write(f"第 {question['position']} 题")
    st.write(question["content"])

    # 历史记录允许自由切题，但不展示提交和结束操作
    if read_only:
        answer = data["current_answer"]
        if answer is None:
            st.info("这道题当时未提交回答。")
        else:
            st.write("已提交的回答：")
            st.text(answer["content"])
            show_answer_feedback(
                api_url,
                token,
                answer["id"],
                session_id=session_id,
            )
        return

    # 完成按钮始终可见，不要求当前页面停留在最后一题
    with st.expander("完成本次练习"):
        unanswered = data["question_count"] - data["answered_count"]
        confirmed = False
        if unanswered:
            st.warning(f"还有 {unanswered} 道未作答。可以点击题号返回作答。")
            confirmed = st.checkbox(
                "我确认结束，未提交的输入不保存为正式回答",
                key=f"finish_confirm_{session_id}_{data['revision']}",
            )
        else:
            st.write("所有题目均已提交，可以完成练习。")
        if st.button("完成本次练习", key=f"finish_{session_id}", disabled=bool(unanswered and not confirmed)):
            try:
                response = httpx.post(
                    f"{api_url}/interview_sessions/{session_id}/finish",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"revision": data["revision"], "confirm_unanswered": confirmed},
                    timeout=10.0,
                )
            except httpx.RequestError:
                st.warning("无法确认结束结果，请重新查询练习列表。")
                return
            if response.status_code == 200:
                result = response.json()
                st.session_state["interview_notice"] = (
                    f"练习已结束：已回答 {result['answered_count']} 道，"
                    f"未作答 {result['unanswered_count']} 道。"
                )
                st.rerun()
            elif response.status_code == 401:
                st.session_state.token = None
                st.rerun()
            else:
                st.warning(response.json().get("detail", "结束失败，请重新读取练习。"))
            return

    answer = data["current_answer"]
    if answer is not None:
        st.success("这道题已提交回答")
        st.text(answer["content"])
        show_answer_feedback(
            api_url,
            token,
            answer["id"],
            session_id=session_id,
        )
        return

    answer_key = f"answer_{session_id}_{question['id']}"
    draft_key = f"draft_{answer_key}"
    widget_key = f"input_{answer_key}"
    if draft_key not in st.session_state:
        st.session_state[draft_key] = ""
    if answer_key not in st.session_state:
        st.session_state[answer_key] = {"submission_id": str(uuid4()), "pending_content": None}

    # 不使用 form：输入离开焦点时先暂存，点击其他题号后也能恢复
    content = st.text_area(
        "你的回答",
        value=st.session_state[draft_key],
        max_chars=1000,
        height=200,
        key=widget_key,
        on_change=save_answer_draft,
        args=(widget_key, draft_key),
    )
    st.caption("切换题号可保留当前页面会话中的草稿；刷新或关闭页面后不保证恢复。点击提交后才保存到数据库。")
    if not st.button("提交本题回答", key=f"submit_{answer_key}", type="primary"):
        return
    if not content.strip():
        st.warning("请先填写回答")
        return

    attempt = st.session_state[answer_key]
    if attempt["pending_content"] != content:
        attempt["submission_id"] = str(uuid4())
        attempt["pending_content"] = content
    try:
        response = httpx.post(
            f"{api_url}/interview_sessions/{session_id}/answers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_record_id": question["id"],
                "submission_id": attempt["submission_id"],
                "revision": data["revision"],
                "content": content,
            },
            timeout=20.0,
        )
    except httpx.RequestError:
        st.warning("无法确认提交结果，请重新打开练习查看；未保存时可以重试。")
        return
    if response.status_code == 200:
        st.rerun()
    elif response.status_code == 401:
        st.session_state.token = None
        st.rerun()
    elif response.status_code == 409:
        st.warning(response.json()["detail"])
        st.info("请点击题号重新读取最新状态。")
    else:
        st.error(f"提交失败：{response.status_code}")



def show_answer_feedback(
    api_url,
    token,
    answer_id,
    is_followup=False,
    session_id=None,
    main_answer_id=None,
):
    if is_followup:
        st.subheader("追问回答点评")
        st.caption("这是巩固练习的点评，与首次主回答分开记录。")
        resource = "interview_followup_answers"
        key_prefix = "followup_feedback"
    else:
        st.subheader("AI 点评")
        resource = "interview_answers"
        key_prefix = "main_feedback"

    url = f"{api_url}/{resource}/{answer_id}/feedback"
    headers = {"Authorization": f"Bearer {token}"}

    # 查询仍使用原来的 GET 接口
    # 主点评的生成操作改由工作流启动接口负责
    if is_followup:
        generate_url = url
    else:
        generate_url = (
            f"{api_url}/interview_sessions/{session_id}"
            f"/answers/{answer_id}/workflow/start"
        )

    # 页面打开时只查询，不自动调用模型
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
    except httpx.RequestError:
        st.warning("暂时无法查询点评，请稍后重新打开。")
        return

    if response.status_code == 401:
        st.session_state.token = None
        st.rerun()

    if response.status_code != 200:
        st.error(f"查询点评失败：{response.status_code}")
        return

    data = response.json()
    status = data["status"]

    if status == "succeeded":
        content = data["feedback_content"]

        if not content["can_evaluate"]:
            st.warning("当前依据不足，无法可靠评价。")

        st.write(content["evaluation_note"])

        # 将 schema 的字段名对应到页面上的中文标题
        sections = {
            "strengths": "回答正确之处",
            "missing_points": "遗漏要点",
            "errors": "错误及解释",
            "suggestions": "改进建议",
        }
        # 不同栏目为空时，使用对应的说明
        if content["can_evaluate"]:
            empty_messages = {
                "strengths": "暂无可明确肯定的要点",
                "missing_points": "未发现需要补充的核心要点",
                "errors": "未发现明确错误",
                "suggestions": "暂无额外改进建议",
            }
        else:
            empty_messages = {
                "strengths": "依据不足，暂不判断",
                "missing_points": "依据不足，暂不判断",
                "errors": "依据不足，暂不判断",
                "suggestions": "请参考上方评价说明",
            }

        for field, title in sections.items():
            st.write(f"**{title}**")
            items = content[field]

            if not items:
                st.caption(empty_messages[field])
            else:
                for item in items:
                    st.write("•", item)
        # 目前只有主点评接入了资料检
        # 当前只有主点评接入资料检索，追问点评暂不展示
        if not is_followup:
            sources = content.get("reference_sources", [])

            st.markdown("**本次提供给 AI 的参考资料**")
            # 读取点评生成时保存的检索状态，不重新发起检索
            retrieval_status = content.get("retrieval_status")
            retrieval_note = content.get("retrieval_note")

            if retrieval_status == "succeeded":
                st.caption("已向 AI 提供检索参考片段。")
            elif retrieval_status == "empty":
                st.info(
                    retrieval_note
                    or "未找到符合条件的片段，本次根据题目和参考要点评价。"
                )
            elif retrieval_status == "failed":
                st.warning(
                    retrieval_note
                    or "资料检索暂不可用，本次根据题目和参考要点评价。"
                )

            if not sources:
                # 兼容没有检索状态字段的旧点评
                if retrieval_status is None:
                    st.caption("本次点评未记录检索参考资料。")
            else:
                st.caption(
                    "以下为生成点评时提供的候选片段，"
                    "不代表 AI 使用了全部片段，也不保证每段都与问题相关。"
                )

                for source in sources:
                    with st.expander(
                        f"[资料{source['number']}] {source['title']}"
                    ):
                        st.caption(
                            f"资料编号：{source['document_id']} · "
                            f"修订号：{source['revision']} · "
                            f"片段：{source['position']}"
                        )

                        st.write(
                            "来源链接：",
                            source.get("source_url") or "未填写",
                        )

                        st.write(
                            "版本说明：",
                            source.get("version_note") or "未填写",
                        )

                        # 显示点评生成时保存的片段，避免混入后来修改的正文
                        st.text(source["content"])
        # 主点评成功后显示追问，追问点评后不再继续追问
        if not is_followup:
            show_answer_followup(api_url, token, answer_id, session_id)

        return

    if status == "processing":
        st.info("点评正在生成中，请稍后刷新结果。")

        if st.button("刷新点评", key=f"refresh_{key_prefix}_{answer_id}"):
            st.rerun()

        return

    if status == "failed":
        st.warning(data["error_message"] or "点评生成失败")
        button_text = "重试点评"
    else:
        button_text = "生成点评"

    if st.button(button_text, key=f"generate_{key_prefix}_{answer_id}"):
        try:
            # 等待上限略长于后端模型客户端的 60 秒超时
            with st.spinner("正在生成点评，请稍候……"):
                if not is_followup:
                    # 主点评：启动工作流
                    response = httpx.post(
                        generate_url,
                        headers=headers,
                        timeout=90.0,
                    )
                else:
                    workflow_url = (
                        f"{api_url}/interview_sessions/{session_id}"
                        f"/answers/{main_answer_id}/workflow"
                    )

                    # 历史记录或后端重启后，可能没有内存检查点
                    response = httpx.post(
                        f"{workflow_url}/start",
                        headers=headers,
                        timeout=90.0,
                    )

                    if response.status_code == 200:
                        stage = response.json()["state"]["stage"]

                        # 已有追问回答，说明用户已选择过练习追问
                        # 恢复检查点时，复用数据库中已生成的追问
                        if stage == "waiting_choice":
                            response = httpx.post(
                                f"{workflow_url}/choice",
                                headers=headers,
                                json={"choice": "generate_followup"},
                                timeout=90.0,
                            )

                    if response.status_code == 200:
                        stage = response.json()["state"]["stage"]

                        if stage == "waiting_followup_answer":
                            # 回答已经通过原接口保存，这里只提交编号
                            response = httpx.post(
                                f"{workflow_url}/answer-ready",
                                headers=headers,
                                json={"followup_answer_id": answer_id},
                                timeout=90.0,
                            )
                        elif stage == "completed":
                            st.info("本题工作流已结束，请重新打开题目查询点评。")
                            return
                        else:
                            st.warning(
                                f"当前流程阶段为 {stage}，暂时无法生成追问点评。"
                            )
                            return
        except httpx.RequestError:
            st.warning(
                "暂时无法确认生成结果，请重新打开题目查询，"
                "不要立即认定生成失败。"
            )
            return

        if response.status_code == 200:
            # 成功或失败状态都从 GET 接口重新读取
            st.rerun()
        elif response.status_code == 401:
            st.session_state.token = None
            st.rerun()
        elif response.status_code in (400, 409):
            st.warning(response.json().get("detail", "请重新读取流程状态"))
        else:
            st.error(f"生成点评请求失败：{response.status_code}")



def show_answer_followup(api_url, token, answer_id, session_id):
    st.subheader("针对性追问")
    st.caption("这是看过主点评后的巩固练习，每道主问题最多一次追问。")

    url = f"{api_url}/interview_answers/{answer_id}/followup"
    headers = {"Authorization": f"Bearer {token}"}

    # 打开页面只查询已有记录，不自动生成
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
    except httpx.RequestError:
        st.warning("暂时无法查询追问，请稍后重新打开。")
        return

    if response.status_code == 401:
        st.session_state.token = None
        st.rerun()

    if response.status_code != 200:
        st.error(f"查询追问失败：{response.status_code}")
        return

    data = response.json()
    status = data["status"]

    if status == "succeeded":
        st.write(data["question_content"])
        show_followup_answer(
            api_url, token, data, session_id, answer_id
        )
        return

    if status == "processing":
        st.info("追问正在生成中，请稍后刷新。")

        if st.button("刷新追问", key=f"refresh_followup_{answer_id}"):
            st.rerun()

        return

    if status == "failed":
        st.warning(data["error_message"] or "追问生成失败")
        button_text = "重试生成追问"
    else:
        button_text = "生成一道追问"

    if st.button(button_text, key=f"generate_followup_{answer_id}"):
        workflow_url = (
            f"{api_url}/interview_sessions/{session_id}"
            f"/answers/{answer_id}/workflow"
        )

        try:
            with st.spinner("正在准备追问……"):
                # 历史记录可能尚未启动工作流；已有进度时只读取
                response = httpx.post(
                    f"{workflow_url}/start",
                    headers=headers,
                    timeout=90.0,
                )

                if response.status_code == 401:
                    st.session_state.token = None
                    st.rerun()

                if response.status_code != 200:
                    st.warning(
                        response.json().get("detail", "无法启动工作流")
                    )
                    return

                stage = response.json()["state"]["stage"]

                if stage == "waiting_choice":
                    # 将按钮操作作为用户选择，恢复第一次暂停
                    response = httpx.post(
                        f"{workflow_url}/choice",
                        headers=headers,
                        json={"choice": "generate_followup"},
                        timeout=90.0,
                    )
                elif stage == "waiting_followup_answer":
                    # 追问已准备好，重新查询并展示数据库中的内容
                    st.rerun()
                else:
                    st.warning(f"当前流程阶段为 {stage}，暂时无法生成追问。")
                    return

        except httpx.RequestError:
            st.warning("无法确认生成结果，请重新打开题目查询。")
            return

        if response.status_code == 200:
            st.rerun()
        elif response.status_code == 401:
            st.session_state.token = None
            st.rerun()
        elif response.status_code in (400, 409):
            st.warning(response.json().get("detail", "请重新读取流程状态"))
        else:
            st.error(f"生成追问请求失败：{response.status_code}")

        



def show_followup_answer(
    api_url, token, followup_data, session_id, main_answer_id
):
    # 已回答时显示数据库内容，不再允许编辑
    saved_answer = followup_data["followup_answer"]

    if saved_answer is not None:
        st.success("追问回答已保存")
        st.text(saved_answer["content"])
        show_answer_feedback(
            api_url,
            token,
            saved_answer["id"],  # 追问回答编号
            is_followup=True,
            session_id=session_id,
            main_answer_id=main_answer_id,
        )
        return

    followup_id = followup_data["followup_id"]

    # 每道追问使用独立状态，不与主回答混淆
    attempt_key = f"followup_attempt_{followup_id}"
    draft_key = f"followup_draft_{followup_id}"
    widget_key = f"followup_input_{followup_id}"

    if draft_key not in st.session_state:
        st.session_state[draft_key] = ""

    if attempt_key not in st.session_state:
        st.session_state[attempt_key] = {
            "submission_id": str(uuid4()),
            "pending_content": None,
        }

    # 复用已有的草稿保存回调
    content = st.text_area(
        "你的追问回答",
        value=st.session_state[draft_key],
        max_chars=1000,
        height=160,
        key=widget_key,
        on_change=save_answer_draft,
        args=(widget_key, draft_key),
    )

    if not st.button(
        "提交追问回答",
        key=f"submit_followup_{followup_id}",
    ):
        return

    if not content.strip():
        st.warning("请先填写追问回答")
        return

    # 内容相同时重试沿用原标识，内容变化则使用新标识
    attempt = st.session_state[attempt_key]
    if attempt["pending_content"] != content:
        attempt["submission_id"] = str(uuid4())
        attempt["pending_content"] = content

    try:
        response = httpx.post(
            f"{api_url}/interview_followups/{followup_id}/answers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "submission_id": attempt["submission_id"],
                "content": content,
            },
            timeout=10.0,
        )
    except httpx.RequestError:
        st.warning("无法确认提交结果，请重新打开题目查看是否已保存。")
        return

    if response.status_code == 200:
        # 重新查询追问，读取刚保存的回答
        st.rerun()
    elif response.status_code == 401:
        st.session_state.token = None
        st.rerun()
    elif response.status_code == 409:
        st.warning(response.json()["detail"])
        st.info("请重新打开题目，读取已保存的回答。")
    elif response.status_code == 422:
        st.error("回答不符合要求，请检查内容和长度。")
    else:
        st.error(f"提交追问回答失败：{response.status_code}")



def show_interview_report(api_url, token, session_id):
    st.subheader("练习总结报告")
    st.caption("报告基于生成时的问答记录，后续补充点评不会自动改写它。")

    url = f"{api_url}/interview_sessions/{session_id}/report"
    headers = {"Authorization": f"Bearer {token}"}

    # 打开页面只查询，不自动调用模型
    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=10.0,
        )
    except httpx.RequestError:
        st.warning("暂时无法查询报告，请稍后重试。")
        return

    if response.status_code == 401:
        st.session_state.token = None
        st.rerun()

    if response.status_code != 200:
        st.error(f"查询报告失败：{response.status_code}")
        return

    data = response.json()
    status = data["status"]

    if status == "succeeded":
        stats = data["statistics"]
        content = data["report_content"]

        st.write(
            f"主问题共 {stats['question_count']} 道，"
            f"已回答 {stats['answered_count']} 道，"
            f"未回答 {stats['unanswered_count']} 道。"
        )

        feedback_count = stats["main_feedback_succeeded_count"]

        st.caption(
            f"本报告生成时，已有 {feedback_count} 份成功的主问题点评。"
        )

        if feedback_count < stats["answered_count"]:
            st.info(
                "部分已回答题目尚无成功点评，本报告依据当时已有的回答和点评生成；"
                "之后补充的点评不会自动更新本报告。"
            )

        if not content["can_summarize"]:
            st.warning("现有材料不足以形成可靠的整体判断。")

        st.write(content["overall_summary"])

        st.write("**表现较好之处**")
        if content["strengths"]:
            for item in content["strengths"]:
                st.write("•", item)
        else:
            st.caption("暂无足够证据支持的总结")

        st.write("**待复习知识点**")
        if content["weak_points"]:
            for item in content["weak_points"]:
                positions = "、".join(
                    str(position)
                    for position in item["question_positions"]
                )
                st.write(
                    f"**{item['knowledge_point']} · 第 {positions} 题**"
                )
                st.write("依据：", item["reason"])
                st.write("建议：", item["suggestion"])
        else:
            st.caption("暂无有可靠证据支持的核心薄弱点")

        st.write("**追问巩固回顾**")
        if content["followup_reviews"]:
            for item in content["followup_reviews"]:
                st.write(
                    f"第 {item['question_position']} 题：",
                    item["observation"],
                )
        else:
            st.caption("暂无追问回顾，不代表所有知识点均已掌握")

        st.write("**整体复习建议**")
        for item in content["study_suggestions"]:
            st.write("•", item)

        return

    if status == "processing":
        st.info("报告正在生成中，请稍后刷新。")
        if st.button("刷新报告", key=f"refresh_report_{session_id}"):
            st.rerun()
        return

    if status == "failed":
        st.warning(data["error_message"] or "报告生成失败")
        button_text = "重试生成报告"
    else:
        st.info("本次练习尚未生成总结报告。")
        button_text = "生成练习报告"

    if st.button(button_text, key=f"generate_report_{session_id}"):
        try:
            with st.spinner("正在总结本次练习，请稍候……"):
                response = httpx.post(
                    url,
                    headers=headers,
                    timeout=90.0,
                )
        except httpx.RequestError:
            st.warning("无法确认生成结果，请重新打开练习查询。")
            return

        if response.status_code == 200:
            # 成功或业务失败，都重新查询数据库中的最终状态
            st.rerun()
        elif response.status_code == 401:
            st.session_state.token = None
            st.rerun()
        elif response.status_code == 409:
            st.warning(response.json().get("detail", "请刷新后重试"))
        else:
            st.error(f"生成报告请求失败：{response.status_code}")




