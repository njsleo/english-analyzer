import streamlit as st
import json
import pandas as pd
import trafilatura
import io
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from openai import OpenAI
from supabase import create_client, Client

# ==========================================
# ⚙️ 核心配置区
# ==========================================
DEEPSEEK_API_KEY = "sk-462830ffe3424e8a820f0bd3aee786b0"
SUPABASE_URL = "https://grtnteyfjbanmdfhwbwg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdydG50ZXlmamJhbm1kZmh3YndnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzODI0MDcsImV4cCI6MjA5MDk1ODQwN30.LqR-QLHKW4Hag71tJLeagYPvOOIyCD7UrWXwfYzwGuU"

llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 🎨 UI/UX 大师级设计系统
# ==========================================
st.set_page_config(page_title="顶级英语教研室", page_icon="🏛️", layout="wide")

custom_css = """
<style>
    [data-testid="stSidebar"] { background-color: #1A1A24 !important; border-right: 1px solid #2D2D3B; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #F0F0F5 !important; }
    div.stRadio > div[role="radiogroup"] > label > div:first-child { background-color: transparent; }
    .stApp { background-color: #FAFAFC; }
    h1, h2, h3 { font-family: 'Times New Roman', '等线', serif !important; color: #1A1A24; }
    div.stButton > button { border-radius: 6px !important; font-weight: 600 !important; border: none !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease; }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔐 用户认证系统 (Auth)
# ==========================================
if 'user' not in st.session_state:
    st.session_state['user'] = None

# 如果用户未登录，显示登录/注册界面并拦截后续代码
if st.session_state['user'] is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🏛️ 顶级英语教研与学习平台</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>赋能每一位英语学习者的智能精读工作台</p>", unsafe_allow_html=True)
    
    col_space1, col_auth, col_space2 = st.columns([1, 1, 1])
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 登录", "📝 注册新账号"])
        
        with tab_login:
            login_email = st.text_input("邮箱地址", key="l_email")
            login_pwd = st.text_input("密码", type="password", key="l_pwd")
            if st.button("登录进入平台", use_container_width=True, type="primary"):
                with st.spinner("正在验证身份..."):
                    try:
                        response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                        st.session_state['user'] = response.user
                        st.rerun()
                    except Exception as e:
                        st.error(f"登录失败，请检查账号密码是否正确。")
                        
        with tab_signup:
            signup_email = st.text_input("常用邮箱", key="s_email")
            signup_pwd = st.text_input("设置密码 (至少6位)", type="password", key="s_pwd")
            if st.button("免费注册", use_container_width=True):
                with st.spinner("正在创建专属空间..."):
                    try:
                        response = supabase.auth.sign_up({"email": signup_email, "password": signup_pwd})
                        st.success("✅ 注册成功！请直接在左侧标签页登录。")
                    except Exception as e:
                        st.error(f"注册失败: {e}")
    st.stop() # 🛑 核心拦截器：未登录者无法执行后面的任何代码

# 提取当前用户的唯一身份证号 (UUID)
CURRENT_USER_ID = st.session_state['user'].id

# ==========================================
# 🕸️ 功能函数区 (爬虫与Word生成)
# ==========================================
def fetch_text_smart(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded: return "❌ 网页下载失败，请手动复制粘贴。"
        text = trafilatura.extract(downloaded)
        return text if text else "⚠️ 未能识别正文，请手动复制粘贴。"
    except Exception as e:
        return f"抓取异常: {e}"

def set_font(run, ascii_font='Times New Roman', east_asia_font='等线'):
    run.font.name = ascii_font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)

def generate_beautiful_word(analysis_data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

    head0 = doc.add_heading('📖 英语精读教案', 0)
    for run in head0.runs: set_font(run)
    head1 = doc.add_heading('一、 逐句语法与词法拆解', level=1)
    for run in head1.runs: set_font(run)

    for i, s in enumerate(analysis_data.get('sentences', [])):
        p_en = doc.add_paragraph()
        run_en = p_en.add_run(f"[{i+1}] {s.get('en', '')}")
        run_en.bold, run_en.font.size = True, Pt(14)
        set_font(run_en)
        p_cn = doc.add_paragraph()
        run_cn = p_cn.add_run(f"译文：{s.get('cn', '')}")
        run_cn.font.size = Pt(11)
        set_font(run_cn)
        
        p_syn = doc.add_paragraph()
        p_syn.paragraph_format.left_indent = Pt(15)
        run_syn_label = p_syn.add_run("🔍 语法拆解：")
        run_syn_label.bold, run_syn_label.font.color.rgb = True, RGBColor(0x1F, 0x4E, 0x79)
        set_font(run_syn_label)
        run_syn_text = p_syn.add_run(s.get('syntax', '').replace('*', '').replace('#', ''))
        set_font(run_syn_text)
        
        clean_words = s.get('words', '').replace('*', '').replace('#', '')
        if clean_words:
            p_word = doc.add_paragraph(style='List Bullet')
            run_word_label = p_word.add_run("💡 核心词法：")
            run_word_label.bold, run_word_label.font.color.rgb = True, RGBColor(0xC0, 0x00, 0x00)
            set_font(run_word_label)
            run_word_text = p_word.add_run(clean_words)
            set_font(run_word_text)

    head2 = doc.add_heading('二、 核心难词与底层逻辑', level=1)
    for run in head2.runs: set_font(run)
    vocab_list = analysis_data.get('core_vocabulary', [])
    if vocab_list:
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text, cells[1].text, cells[2].text, cells[3].text = '单词', '音标', '中文释义', '底层记忆法 & 专家例句'
        for v in vocab_list:
            r_cells = table.add_row().cells
            r_cells[0].text, r_cells[1].text, r_cells[2].text = v.get('word', ''), v.get('phonetic', ''), v.get('translation', '')
            r_cells[3].text = f"【记忆】{v.get('memory_tip', '').replace('*', '')}\n\n【例句】{v.get('usage_examples', '').replace('*', '')}"
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs: set_font(run)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ==========================================
# 🧭 主界面与导航
# ==========================================
st.sidebar.markdown("## 🏛️ 教授工作台")
st.sidebar.markdown("---")
page = st.sidebar.radio("核心功能导航：", ["🔍 1. 智能精读教研室", "🗂️ 2. 文章分类档案馆", "🔠 3. 词汇分级记忆库"])

st.sidebar.markdown("---")
st.sidebar.caption(f"👤 登录账号:\n{st.session_state['user'].email}")
if st.sidebar.button("🚪 安全退出"):
    st.session_state['user'] = None
    st.rerun()

# ------------------------------------------
# 模块 1：智能精读室 (插入数据时带上 user_id)
# ------------------------------------------
if page == "🔍 1. 智能精读教研室":
    st.title("🔍 智能精读教研室")
    col_input1, col_input2 = st.columns([3, 1])
    with col_input1: url = st.text_input("🔗 输入英文文章链接 (自动剥离广告)：")
    with col_input2:
        st.write(""); st.write("")
        if st.button("🛰️ 一键提取正文", use_container_width=True):
            if url:
                with st.spinner("正在提取..."): st.session_state['temp_text'] = fetch_text_smart(url)
    
    final_text = st.text_area("📝 待分析纯净文本：", value=st.session_state.get('temp_text', ""), height=150)

    if st.button("🧠 生成逐句专家级教案", type="primary"):
        if not final_text.strip() or final_text.startswith("❌"): st.error("请输入有效文本！")
        else:
            with st.spinner("特级教师正在逐句切片，请稍候..."):
                system_prompt = "你是一位精通英语语法的特级教师。请将文章逐句彻底拆解。"
                user_prompt = f"""
                必须严格以 JSON 格式输出：
                {{
                    "sentences": [
                        {{"en": "原句英文", "cn": "翻译", "syntax": "极简语法拆解", "words": "本句核心词及搭配"}}
                    ],
                    "core_vocabulary": [
                        {{"word": "单词", "phonetic": "音标", "translation": "释义", "memory_tip": "词根词缀", "usage_examples": "造句", "tags": "四级/六级/托福/雅思"}}
                    ]
                }}
                待分析：\n{final_text}
                """
                try:
                    response = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], response_format={"type": "json_object"})
                    st.session_state['analysis_result'] = json.loads(response.choices[0].message.content)
                    st.session_state['article_content'] = final_text
                    st.rerun() 
                except Exception as e: st.error(f"分析失败: {e}")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        st.divider()
        st.markdown("### 📥 导出与个人云端归档")
        action_col1, action_col2, action_col3 = st.columns([2, 2, 2])
        with action_col1:
            st.download_button("📝 1. 导出精美 Word 教案", data=generate_beautiful_word(res), file_name="精读教案.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with action_col2:
            selected_category = st.selectbox("📂 2. 为本文选择分类：", ["新闻时事", "学术论文", "名著小说", "考试阅读", "日常应用", "未分类"], label_visibility="collapsed")
        with action_col3:
            if st.button("☁️ 3. 同步至我的私人题库", use_container_width=True):
                try:
                    formatted_txt = "".join([f"[{i+1}] {s.get('en','')}\n译：{s.get('cn','')}\n语法：{s.get('syntax','')}\n\n" for i, s in enumerate(res.get('sentences', []))])
                    # ⚠️ 核心修改：写入数据库时打上用户专属烙印
                    supabase.table('articles').insert({
                        "user_id": CURRENT_USER_ID,
                        "content": st.session_state['article_content'],
                        "translation": "逐句精读见教案",
                        "teaching_plan": formatted_txt,
                        "category": selected_category
                    }).execute()
                    
                    if res.get('core_vocabulary'):
                        for v in res['core_vocabulary']:
                            v["user_id"] = CURRENT_USER_ID # 单词也打上烙印
                            supabase.table('vocabulary').insert(v).execute()
                    st.success("✅ 保存成功！已存入您的私人空间。")
                except Exception as e: st.error(f"保存失败: {e}")

        # 网页端预览
        st.markdown("### 💻 网页端效果预览")
        for i, s in enumerate(res.get('sentences', [])):
            html_block = f"""
            <div style="background-color: #ffffff; border: 1px solid #EAECEF; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-family: 'Times New Roman', serif; font-size: 1.1em; font-weight: bold; color: #111; margin-bottom: 4px;">[{i+1}] {s.get('en', '')}</div>
                <div style="font-family: '等线', sans-serif; font-size: 0.95em; color: #555; margin-bottom: 8px;">译：{s.get('cn', '')}</div>
                <div style="font-size: 0.9em; color: #222; margin-bottom: 4px;"><span style="color: #1F4E79; font-weight: 600;">🔍 语法：</span>{s.get('syntax', '').replace('*', '').replace('#', '')}</div>
                <div style="font-size: 0.9em; color: #222;"><span style="color: #C00000; font-weight: 600;">💡 词法：</span>{s.get('words', '').replace('*', '').replace('#', '')}</div>
            </div>
            """
            st.markdown(html_block, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🔠 核心难词深度解析")
        if res.get('core_vocabulary'):
            st.dataframe(pd.DataFrame(res['core_vocabulary'])[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)

# ------------------------------------------
# 模块 2：文章档案馆 (只读取当前用户数据)
# ------------------------------------------
elif page == "🗂️ 2. 文章分类档案馆":
    st.title("🗂️ 私人文章档案馆")
    try:
        # ⚠️ 核心修改：只查询 user_id 等于当前登录用户的数据
        arts_data = supabase.table('articles').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data)
            categories = ["全部"] + list(df_arts['category'].dropna().unique()) if 'category' in df_arts.columns else ["全部"]
            cat_filter = st.selectbox("📌 按文章体裁筛选：", categories)
            filtered_arts = df_arts[df_arts['category'] == cat_filter].to_dict('records') if cat_filter != "全部" else arts_data
            
            for i, a in enumerate(filtered_arts):
                with st.expander(f"📖 [{a.get('category', '未分类')}] {a.get('content', '')[:60]}..."):
                    st.text(a.get('teaching_plan', '无'))
        else: st.info("您的私人档案馆空空如也。")
    except Exception as e: st.error(f"读取数据失败: {e}")

# ------------------------------------------
# 模块 3：词汇记忆库 (只读取当前用户数据)
# ------------------------------------------
elif page == "🔠 3. 词汇分级记忆库":
    st.title("🔠 私人专属词汇库")
    try:
        # ⚠️ 核心修改：只查询 user_id 等于当前登录用户的数据
        vocab_data = supabase.table('vocabulary').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data)
            tags = ["全部"] + list(df_vocab['tags'].dropna().unique())
            tag_filter = st.selectbox("🎓 按考试等级/分类筛选：", tags)
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            
            st.metric("您的专属生词量", len(display_df))
            st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
            st.download_button(f"📥 导出私人词汇表", display_df.to_csv(index=False).encode('utf-8-sig'), f"My_Vocabulary.csv", "text/csv")
        else: st.info("您还没有收藏过单词哦。")
    except Exception as e: st.error(f"读取词汇失败: {e}")