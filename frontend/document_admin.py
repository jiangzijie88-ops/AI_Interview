from ui import page_heading, status_label
import httpx
import streamlit as st


def show_document_admin(api_url: str, token: str):
    page_heading("资料管理", "从可信资料到检索依据：导入、审核，再建立索引。")

    # 取出上一次保存后的提示，显示一次后移除
    notice = st.session_state.pop("document_notice", None)
    if notice:
        st.success(notice)

    # 每个请求都携带登录凭证，供后端验证管理员身份
    headers = {"Authorization": f"Bearer {token}"}

    section = st.radio("资料工作区", ["资料列表", "新增与导入", "索引与检索"], horizontal=True, key="document_admin_section")
    if section == "新增与导入":
        _show_document_create(api_url, token, headers)
    elif section == "索引与检索":
        _show_document_tools(api_url, token, headers)
    else:
        _show_document_list(api_url, token, headers)


def _show_document_tools(api_url, token, headers):
    with st.expander("资料索引"):
        st.caption("资料新增、修改或审核状态变化后，需要重新建立索引。")

        if st.button("重建资料索引", key="document_index_rebuild"):
            try:
                with st.spinner("正在切分、向量化并保存索引，请稍候……"):
                    response = httpx.post(
                        f"{api_url}/knowledge_documents/index/rebuild",
                        headers=headers,
                        timeout=180.0,
                    )

                if response.status_code == 200:
                    result = response.json()
                    st.success(
                        f"索引已建立：{result['document_count']} 篇资料，"
                        f"{result['chunk_count']} 个片段"
                    )
                elif response.status_code == 400:
                    st.warning(response.json()["detail"])
                elif response.status_code in (401, 403):
                    st.warning("请使用有效的管理员账号登录")
                else:
                    st.error(f"建立失败，状态码：{response.status_code}")

            except httpx.RequestError:
                st.error("请求未成功完成，请查看后端日志确认执行结果")

    with st.expander("检索参考资料"):
        with st.form("document_search_form"):
            search_query = st.text_input(
                "检索问题",
                max_chars=500,
                placeholder="例如：LangGraph 的节点必须返回完整状态吗？",
            )

            search_k = st.number_input(
                "最多返回片段数",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
            )

            search_submitted = st.form_submit_button("检索")

        if search_submitted:
            if not search_query.strip():
                st.warning("请输入检索问题")
            else:
                try:
                    with st.spinner("正在检索……"):
                        response = httpx.get(
                            f"{api_url}/knowledge_documents/search",
                            headers=headers,
                            params={
                                "query": search_query.strip(),
                                "k": search_k,
                            },
                            timeout=90.0,
                        )

                    if response.status_code == 200:
                        result = response.json()
                        st.write("返回片段数：", result["count"])

                        if not result["items"]:
                            st.info("未找到符合条件的参考片段，可能是相关性不足、资料未审核或索引需要更新。")

                        for index, item in enumerate(result["items"], start=1):
                            metadata = item["metadata"]

                            st.markdown(
                                f"**结果 {index}：{metadata['title']}**"
                            )
                            st.caption(
                                f"资料编号：{metadata['document_id']} · "
                                f"修订号：{metadata['revision']} · "
                                f"片段：{metadata['position']}"
                            )
                            distance = metadata.get("distance")

                            if distance is not None:
                                st.caption(
                                    f"检索距离：{distance:.4f}（越小越接近）"
                                )

                            with st.expander("查看片段正文"):
                                st.text(item["content"])

                            # 纯文本显示来源，避免直接拼接成 Markdown
                            st.write(
                                "来源：",
                                metadata.get("source_url") or "未填写",
                            )
                            st.divider()

                    elif response.status_code == 400:
                        st.warning(response.json()["detail"])
                    elif response.status_code in (401, 403):
                        st.warning("请使用有效的管理员账号登录")
                    else:
                        st.error(f"检索失败，状态码：{response.status_code}")

                except httpx.RequestError:
                    st.error("请求未成功完成，请稍后重试")



def _show_document_create(api_url, token, headers):
    # 收起表单，避免正文输入框占据太多页面空间
    with st.expander("新增参考资料"):
        with st.form("document_create_form", clear_on_submit=False):
            uploaded_file = st.file_uploader(
                "选择 Markdown / TXT 文件（选填）",
                type=["md", "txt"],
                help="支持 UTF-8 编码；选择文件后，以文件内容作为正文。",
                key="document_import_file",
            )
            title = st.text_input("资料标题", max_chars=200)

            content = st.text_area(
                "资料正文",
                height=250,
                max_chars=10000,
                help="未选择文件时使用这里的正文；选择文件后使用文件内容。",
            )

            source_url = st.text_input(
                "来源链接（选填）",
                max_chars=1000,
            )

            version_note = st.text_input(
                "版本说明（选填）",
                max_chars=200,
                help="例如：Python 3.11 官方文档笔记",
            )

            submitted = st.form_submit_button("保存为草稿")

        if submitted:
            import_error = None

            if uploaded_file is not None:
                # 先限制字节大小，避免读取过大的文件
                if uploaded_file.size > 1024 * 1024:
                    import_error = "文件不能超过 1 MB，请按主题拆分后导入。"
                else:
                    try:
                        # utf-8-sig 同时支持普通 UTF-8 和带 BOM 的 UTF-8
                        content = uploaded_file.getvalue().decode("utf-8-sig")
                    except UnicodeDecodeError:
                        import_error = "文件编码不是 UTF-8，请在编辑器中另存为 UTF-8。"

            if import_error:
                st.error(import_error)
            elif len(content) > 10000:
                st.error("正文不能超过 10000 个字符，请按主题拆分后导入。")
            elif not title.strip() or not content.strip():
                st.error("标题和正文不能为空")
            else:
                try:
                    response = httpx.post(
                        f"{api_url}/knowledge_documents",
                        headers=headers,
                        json={
                            "title": title.strip(),
                            # 保留正文原来的换行和代码缩进
                            "content": content,
                            "source_url": source_url.strip() or None,
                            "version_note": version_note.strip() or None,
                        },
                        timeout=10.0,
                    )

                    if response.status_code == 201:
                        document = response.json()
                        st.success(
                            f"资料已保存为草稿，编号：{document['id']}"
                        )
                    elif response.status_code == 401:
                        st.warning("登录已过期，请重新登录")
                    elif response.status_code == 403:
                        st.warning("只有管理员可以新增资料")
                    elif response.status_code == 422:
                        st.error("资料格式不符合要求，请检查输入内容")
                    else:
                        st.error(
                            f"保存失败，状态码：{response.status_code}"
                        )

                except httpx.RequestError:
                    st.error("请求未成功完成，请先检查资料列表，确认是否已保存")



def _show_document_list(api_url, token, headers):
    page = st.number_input(
        "资料列表页码",
        min_value=1,
        value=1,
        step=1,
        key="document_list_page",
    )

    try:
        response = httpx.get(
            f"{api_url}/knowledge_documents",
            headers=headers,
            params={
                "page": page,
                "page_size": 10,
            },
            timeout=10.0,
        )
    except httpx.RequestError:
        st.error("无法连接后端，请稍后重试")
        return

    if response.status_code == 401:
        st.warning("登录已过期，请重新登录")
        return

    if response.status_code == 403:
        st.warning("只有管理员可以管理资料")
        return

    if response.status_code != 200:
        st.error(f"查询资料失败，状态码：{response.status_code}")
        return

    # 将后端返回的 JSON 转换为 Python 字典
    data = response.json()

    st.write("资料总数：", data["total"])

    if not data["items"]:
        st.info("当前页没有资料")
        return

    # 将资料概要显示为表格
    rows = [{"编号": item["id"], "标题": item["title"],
             "状态": status_label(item["status"]), "修订号": item["revision"],
             "版本说明": item["version_note"] or "未填写"} for item in data["items"]]
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
    )

    # 建立“资料编号 → 资料标题”的对应关系
    document_titles = {
        item["id"]: item["title"]
        for item in data["items"]
    }

    selected_id = st.selectbox(
        "选择要查看的资料",
        options=[None] + list(document_titles),
        format_func=lambda document_id: (
            "请选择"
            if document_id is None
            else f"{document_id} · {document_titles[document_id]}"
        ),
        key="document_detail_select",
    )

    # 没有选择时，不请求详情接口
    if selected_id is None:
        return

    try:
        response = httpx.get(
            f"{api_url}/knowledge_documents/{selected_id}",
            headers=headers,
            timeout=10.0,
        )
    except httpx.RequestError:
        st.error("无法连接后端，请稍后重试")
        return

    if response.status_code == 401:
        st.warning("登录已过期，请重新登录")
        return

    if response.status_code == 403:
        st.warning("只有管理员可以查看资料")
        return

    if response.status_code == 404:
        st.warning("这份资料不存在，请刷新列表")
        return

    if response.status_code != 200:
        st.error(f"读取详情失败，状态码：{response.status_code}")
        return

    document = response.json()

    st.subheader(document["title"])
    st.write("状态：", status_label(document["status"]))
    st.write("修订号：", document["revision"])
    st.write("来源链接：", document["source_url"] or "未填写")
    st.write("版本说明：", document["version_note"] or "未填写")

    st.markdown("**资料正文**")

    # 按纯文本显示正文，保留换行，不将资料内容当成页面 Markdown
    with st.expander("查看完整正文"):
        st.text(document["content"])

    with st.expander("资料切分预览"):
        st.caption("预览数据库中已保存的正文，不保存片段，也不调用大模型。")

        if st.button(
            "预览切分结果",
            key=f"document_chunks_{selected_id}",
        ):
            try:
                response = httpx.get(
                    f"{api_url}/knowledge_documents/{selected_id}/chunks",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    preview = response.json()

                    st.write("资料修订号：", preview["revision"])
                    st.write("片段数量：", preview["chunk_count"])

                    # 按顺序显示每个片段
                    for chunk in preview["chunks"]:
                        st.markdown(
                            f"**片段 {chunk['position']} · "
                            f"{chunk['character_count']} 个字符**"
                        )

                        # 纯文本显示，保留正文换行
                        st.text(chunk["content"])
                        st.divider()

                elif response.status_code == 401:
                    st.warning("登录已过期，请重新登录")
                elif response.status_code == 403:
                    st.warning("只有管理员可以预览资料")
                elif response.status_code == 404:
                    st.warning("资料不存在")
                else:
                    st.error(
                        f"切分预览失败，状态码：{response.status_code}"
                    )

            except httpx.RequestError:
                st.error("无法连接后端，请稍后重试")

    st.markdown("**资料审核**")
    st.caption("审核通过表示你已检查资料内容及来源。")

    approve_column, disable_column = st.columns(2)

    with approve_column:
        approve_clicked = st.button(
            "审核通过",
            disabled=document["status"] == "approved",
            key=f"document_approve_{selected_id}",
        )

    with disable_column:
        disable_clicked = st.button(
            "停用资料",
            disabled=document["status"] == "disabled",
            key=f"document_disable_{selected_id}",
        )

    # 根据点击的按钮确定目标状态
    target_status = None

    if approve_clicked:
        target_status = "approved"
    elif disable_clicked:
        target_status = "disabled"

    # 只有点击按钮后，才发送修改请求
    if target_status is not None:
        try:
            response = httpx.patch(
                f"{api_url}/knowledge_documents/{selected_id}/status",
                headers=headers,
                json={"status": target_status},
                timeout=10.0,
            )

            if response.status_code == 200:
                st.session_state.document_notice = (
                    "资料已审核通过"
                    if target_status == "approved"
                    else "资料已停用"
                )
                st.rerun()
            elif response.status_code == 401:
                st.warning("登录已过期，请重新登录")
            elif response.status_code == 403:
                st.warning("只有管理员可以审核资料")
            elif response.status_code == 404:
                st.warning("资料不存在")
            else:
                st.error(f"修改状态失败，状态码：{response.status_code}")

        except httpx.RequestError:
            st.error("请求未成功完成，请重新查询详情确认资料状态")

    with st.expander("编辑这份资料"):
        # 不同资料、不同修订号使用不同表单，避免沿用旧的输入内容
        edit_key = f"document_edit_{document['id']}_{document['revision']}"

        with st.form(edit_key):
            edit_title = st.text_input(
                "资料标题",
                value=document["title"],
                max_chars=200,
            )

            edit_content = st.text_area(
                "资料正文",
                value=document["content"],
                height=300,
                max_chars=10000,
            )

            edit_source_url = st.text_input(
                "来源链接（选填）",
                value=document["source_url"] or "",
                max_chars=1000,
            )

            edit_version_note = st.text_input(
                "版本说明（选填）",
                value=document["version_note"] or "",
                max_chars=200,
            )

            st.caption("保存修改后，资料会退回草稿，需要重新审核。")
            edit_submitted = st.form_submit_button("保存修改")

        if edit_submitted:
            if not edit_title.strip() or not edit_content.strip():
                st.error("标题和正文不能为空")
            else:
                try:
                    response = httpx.put(
                        f"{api_url}/knowledge_documents/{selected_id}",
                        headers=headers,
                        json={
                            "title": edit_title.strip(),
                            "content": edit_content,
                            "source_url": edit_source_url.strip() or None,
                            "version_note": edit_version_note.strip() or None,
                        },
                        timeout=10.0,
                    )

                    if response.status_code == 200:
                        st.session_state.document_notice = "资料已修改，请重新审核"
                        st.rerun()
                    elif response.status_code == 401:
                        st.warning("登录已过期，请重新登录")
                    elif response.status_code == 403:
                        st.warning("只有管理员可以编辑资料")
                    elif response.status_code == 404:
                        st.warning("资料不存在")
                    elif response.status_code == 422:
                        st.error("资料格式不符合要求，请检查输入")
                    else:
                        st.error(f"保存失败，状态码：{response.status_code}")

                except httpx.RequestError:
                    st.error("请求未成功完成，请重新查询详情确认是否已保存")

