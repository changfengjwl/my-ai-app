import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import pandas as pd
from duckduckgo_search import DDGS  # 🌟 导入搜索库

load_dotenv()

st.set_page_config(page_title="长风的AI助手", page_icon="🌪️")
st.title("🌪️ 长风专属 AI 助手")

try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    api_key = os.getenv("DEEPSEEK_API_KEY")

# ==========================================
# 1. 侧边栏基础设置
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")

    # 💡【必懂】：联网搜索开关
    enable_web_search = st.toggle("🌐 开启联网搜索", value=False)

    role = st.selectbox(
        "请选择 AI 的角色：",
        ["简洁幽默的助手", "暴躁老哥", "资深 Python 导师", "文档阅读专家", "翻译官"]
    )

    uploaded_file = st.file_uploader("上传文档 (PDF, TXT, CSV, Excel)", type=["pdf", "txt", "csv", "xlsx"])

    if st.button("🗑️ 清空当前对话"):
        st.session_state.messages = [{"role": "system", "content": f"你现在的角色是：{role}。"}]
        st.rerun()

# ==========================================
# 2. 处理文件
# ==========================================
document_text = ""
if uploaded_file is not None:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_ext == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    document_text += text + "\n"
        elif file_ext == "txt":
            document_text = uploaded_file.read().decode('utf-8')
        elif file_ext in ["csv", "xlsx"]:
            if file_ext == "csv":
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.session_state.df = df
            document_text = df.to_csv(index=False)

            if len(document_text) == 0:
                st.warning("⚠️ 表格读取成功，但里面好像是空的。")
            else:
                st.info(f"📊 表格识别成功！共 {len(df)} 行数据，{len(df.columns)} 列。")

        if len(document_text) > 0:
            st.success(f"✅ 成功读取文件：{uploaded_file.name}，共 {len(document_text)} 个字符！")
    except Exception as e:
        st.error(f"读取文件失败了，报错如下：{e}")

# ==========================================
# 3. 数据可视化与下载
# ==========================================
with st.sidebar:
    if "df" in st.session_state:
        st.markdown("---")
        st.subheader("📈 数据可视化")
        chart_type = st.selectbox("选择图表类型", ["不生成", "柱状图", "折线图"])
        if chart_type != "不生成":
            x_col = st.selectbox("选择 X 轴", st.session_state.df.columns)
            if chart_type == "柱状图":
                st.bar_chart(st.session_state.df.set_index(x_col))
            elif chart_type == "折线图":
                st.line_chart(st.session_state.df.set_index(x_col))

        st.markdown("---")
        st.subheader("📥 导出数据")
        csv_data = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="点击下载处理好的 CSV",
            data=csv_data,
            file_name="处理后的数据.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.caption("Powered by 长风 🌪️ | 我的第一个 AI 产品")


# ==========================================
# 4. AI 聊天逻辑 (🌟 修复了你的嵌套错误)
# ==========================================
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

# 核心聊天触发区
if prompt := st.chat_input("请输入你的问题..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考..."):
            try:
                # 联网搜索逻辑
                search_context = ""
                if enable_web_search:
                    with st.spinner("🔍 正在全网搜索最新信息..."):
                        results = DDGS().text(prompt, max_results=3)
                        for res in results:
                            search_context += f"- {res['title']}: {res['body']}\n"

                temp_messages = st.session_state.messages.copy()

                # 组装上下文
                sys_content = ""
                if document_text:
                    sys_content += f"以下是参考文档：\n{document_text}\n\n"
                if search_context:
                    sys_content += f"以下是联网搜索到的最新信息：\n{search_context}\n\n"

                if sys_content:
                    temp_messages.insert(1, {
                        "role": "system",
                        "content": f"请根据以下背景信息回答用户：\n{sys_content}"
                    })

                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=temp_messages
                )
                answer = response.choices[0].message.content
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"出错了：{e}")