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
    .stApp {font-family:"PingFang SC","Microsoft YaHei",sans-serif;}
    .block-container {max-width:1120px;padding-top:2.5rem;padding-bottom:4rem;}
    [data-testid="stSidebar"] {border-right:1px solid #dce6e9;}
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        justify-content:flex-start;min-height:46px;padding-left:18px;
    }
    [data-testid="stForm"] {border:1px solid #dce6e9;border-radius:16px;
        padding:1.7rem;background:white;}
    [data-testid="stExpander"] {border-radius:10px;background:white;}
    h1 {font-size:2rem!important;letter-spacing:-0.035em;color:#182b36;}
    h2,h3 {letter-spacing:-0.02em;color:#182b36;}
    p {line-height:1.75;}
    button {border-radius:8px!important;min-height:42px;}
    button:focus-visible,a:focus-visible {outline:3px solid #087e83!important;outline-offset:3px;}
    .practice-intro {background:#183b46;color:#fff;padding:36px 40px;
        border-radius:18px;margin-bottom:28px;}
    .practice-intro h1 {color:#fff;font-size:2.25rem!important;margin:0 0 12px;}
    .practice-intro p {color:#d3e6e8;max-width:38em;margin:0;}
    .practice-path {display:flex;gap:24px;flex-wrap:wrap;border-top:1px solid #42616a;
        padding-top:20px;margin-top:24px;color:#e2efef;font-size:14px;}
    .brand-mark {border-left:4px solid #087e83;padding-left:14px;margin:12px 0 28px;}
    .brand-mark strong {font-size:21px;color:#182b36;}
    .brand-mark p {font-size:13px;color:#647780;margin:4px 0 0;}
    @media(max-width:640px) {
        .block-container {padding:1.2rem 1rem 2rem;}
        .practice-intro {padding:24px;border-radius:12px;}
        .practice-intro h1 {font-size:1.7rem!important;}
        [data-testid="stForm"] {padding:1rem;}
        .practice-path {gap:12px;}
    }
    [data-testid="stText"] {white-space:pre-wrap;overflow-wrap:anywhere;}
    </style>""", unsafe_allow_html=True)


def page_heading(title, description):
    st.title(title)
    st.caption(description)


def practice_intro():
    """首页的静态引导区；不读取数据，也不改变练习流程。"""
    st.markdown("""
    <section class="practice-intro">
        <h1>把每一次回答，练得更清楚。</h1>
        <p>选一个方向，认真回答。通过点评找到遗漏，再用针对性追问巩固理解。</p>
        <div class="practice-path">
            <span>选择练习方向</span><span>逐题回答与点评</span><span>回看总结与建议</span>
        </div>
    </section>
    """, unsafe_allow_html=True)
