"""界面公共设置：这里只处理展示，不包含业务请求。"""

import streamlit as st

STATUS_NAMES = {
    "draft": "草稿", "approved": "已审核", "disabled": "已停用",
    "in_progress": "进行中", "completed": "已完成", "ended_early": "提前结束",
}
DIFFICULTY_NAMES = {"basic": "基础", "advanced": "进阶"}


def status_label(value):
    return STATUS_NAMES.get(value, value)


def difficulty_label(value):
    return DIFFICULTY_NAMES.get(value, value)


def setup_page():
    st.set_page_config(page_title="AI 面试平台", page_icon="💬", layout="wide")
    # 只使用稳定的容器选择器，表单和内容使用 Streamlit 原生组件。
    st.markdown("""<style>
    .block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
    [data-testid="stSidebar"] {border-right:1px solid #e2e8f0;}
    [data-testid="stForm"] {border-radius:14px;padding:1.4rem;background:white;}
    [data-testid="stExpander"] {border-radius:12px;background:white;}
    h1 {font-size:2rem!important;letter-spacing:-0.03em;}
    h2,h3 {letter-spacing:-0.02em;}
    button {border-radius:9px!important;}
    [data-testid="stText"] {white-space:pre-wrap;overflow-wrap:anywhere;}
    </style>""", unsafe_allow_html=True)


def page_heading(title, description):
    st.title(title)
    st.caption(description)
