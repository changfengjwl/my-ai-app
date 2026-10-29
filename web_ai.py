import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

# 尝试加载本地的 .env 文件（云端没有这个文件也没关系，不会报错）
load_dotenv()

# --- 页面基础设置 ---
st.set_page_config(page_title="长风的AI助手", page_icon="🌪️")
st.title("🌪️ 长风专属 AI 助手")

# --- 🌟 核心兼容写法：优先去云端保险箱找 Key，找不到再用本地 .env 的 ---
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    api_key = os.getenv("DEEPSEEK_API_KEY")

# --- 侧边栏设置 ---
with st.sidebar:
    st.header("⚙️ 设置")

    # 1. 角色选择
    role = st.selectbox(
        "请选择 AI 的角色：",
        ["简洁幽默的助手", "暴躁老哥", "资深 Python 导师", "文档阅读专家", "翻译官"]
    )

    # 2. 上传文件组件
    uploaded_file = st.file_uploader("上传一个文档 (PDF 或 TXT)", type=["pdf", "txt"])

    # 3. 清空对话按钮
    if st.button("🗑️ 清空当前对话"):
        st.session_state.messages = [
            {"role": "system", "content": f"你现在的角色是：{role}。"}
        ]
        st.rerun()

    st.markdown("---")
    st.caption("Powered by 长风 🌪️ | 我的第一个 AI 产品")

# --- 处理上传的文件 ---
document_text = ""
if uploaded_file is not None:
    if uploaded_file.name.endswith('.pdf'):
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            document_text += page.extract_text() + "\n"
    elif uploaded_file.name.endswith('.txt'):
        document_text = uploaded_file.read().decode('utf-8')

    st.success(f"✅ 成功读取文件：{uploaded_file.name}，共 {len(document_text)} 个字符！")


# --- 初始化 AI 客户端 ---
@st.cache_resource
def get_client(key):
    return OpenAI(
        api_key=key,
        base_url="https://api.deepseek.com"
    )


client = get_client(api_key)

# --- 初始化对话历史 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": f"你现在的角色是：{role}。"}
    ]

# --- 显示历史对话 ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# --- 底部输入框与 AI 交互 ---
if prompt := st.chat_input("请输入你的问题..."):

    # 1. 把用户输入显示在界面上并存入历史
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 调用 AI
    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考..."):
            try:
                # 复制一份历史记录，避免污染全局状态
                temp_messages = st.session_state.messages.copy()

                # 如果上传了文档，就把文档内容插到 system 角色后面
                if document_text:
                    temp_messages.insert(1, {
                        "role": "system",
                        "content": f"你需要根据以下文档内容来回答用户的问题：\n\n{document_text}"
                    })

                # 发送请求
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=temp_messages
                )
                answer = response.choices[0].message.content
                st.write(answer)

                # 3. 把 AI 回答存入历史
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"出错了：{e}")