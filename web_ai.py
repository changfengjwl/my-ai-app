import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import pandas as pd  # 🌟 必须有这行的

load_dotenv()

st.set_page_config(page_title="长风的AI助手", page_icon="🌪️")
st.title("🌪️ 长风专属 AI 助手")

try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    api_key = os.getenv("DEEPSEEK_API_KEY")

with st.sidebar:
    st.header("⚙️ 设置")
    role = st.selectbox(
        "请选择 AI 的角色：",
        ["简洁幽默的助手", "暴躁老哥", "资深 Python 导师", "文档阅读专家", "翻译官"]
    )

    uploaded_file = st.file_uploader("上传文档 (PDF, TXT, CSV, Excel)", type=["pdf", "txt", "csv", "xlsx"])

    if st.button("🗑️ 清空当前对话"):
        st.session_state.messages = [{"role": "system", "content": f"你现在的角色是：{role}。"}]
        st.rerun()

    st.markdown("---")
    st.caption("Powered by 长风 🌪️ | 我的第一个 AI 产品")

document_text = ""
if uploaded_file is not None:
    # 获取文件后缀名，比如 'xlsx'
    file_ext = uploaded_file.name.split(".")[-1].lower()

    try:
        # 🌟 处理 PDF
        if file_ext == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    document_text += text + "\n"

        # 🌟 处理 TXT
        elif file_ext == "txt":
            document_text = uploaded_file.read().decode('utf-8')

        # 🌟 处理 CSV 和 Excel
        elif file_ext in ["csv", "xlsx"]:
            if file_ext == "csv":
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # 把表格转成纯文本
            document_text = df.to_csv(index=False)

            if len(document_text) == 0:
                st.warning("⚠️ 表格读取成功，但里面好像是空的（或者数据不在第一个Sheet里）。")
            else:
                st.info(f"📊 表格识别成功！共 {len(df)} 行数据，{len(df.columns)} 列。")

        # 检查最终提取的文本长度
        if len(document_text) > 0:
            st.success(f"✅ 成功读取文件：{uploaded_file.name}，共 {len(document_text)} 个字符！")
        else:
            st.error(f"⚠️ 成功打开文件，但没有提取到任何文字。请检查文件内容是否在第一页。")

    except Exception as e:
        st.error(f"读取文件失败了，报错如下：{e}")


@st.cache_resource
def get_client(key):
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


client = get_client(api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": f"你现在的角色是：{role}。"}]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

if prompt := st.chat_input("请输入你的问题..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考..."):
            try:
                temp_messages = st.session_state.messages.copy()
                if document_text:
                    sys_prompt = f"请根据以下文档/表格内容回答用户问题：\n\n{document_text}"
                    temp_messages.insert(1, {"role": "system", "content": sys_prompt})

                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=temp_messages
                )
                answer = response.choices[0].message.content
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"出错了：{e}")