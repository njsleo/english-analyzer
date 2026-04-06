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
# 🕸️ 智能网页抓取
# ==========================================
def fetch_text_smart(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded: return "❌ 网页下载失败，请手动复制粘贴。"
        text = trafilatura.extract(downloaded)
        return text if text else "⚠️ 未能识别正文，请手动复制粘贴。"
    except Exception as e:
        return f"抓取异常: {e}"

# ==========================================
# 📝 生成出版级 Word 文档
# ==========================================
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

    sentences = analysis_data.get('sentences', [])
    for i, s in enumerate(sentences):
        p_en = doc.add_paragraph()
        run_en = p_en.add_run(f"[{i+1}] {s.get('en', '')}")
        run_en.bold = True
        run_en.font.size = Pt(14)
        set_font(run_en)
        
        p_cn = doc.add_paragraph()
        run_cn = p_cn.add_run(f"译文：{s.get('cn', '')}")
        run_cn.font.size = Pt(11)
        set_font(run_cn)
        
        clean_syntax = s.get('syntax', '').replace('*', '').replace('#', '')
        p_syn = doc.add_paragraph()
        p_syn.paragraph_format.left_indent = Pt(15)
        run_syn_label = p_syn.add_run("🔍 语法拆解：")
        run_syn_label.bold = True
        run_syn_label.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        set_font(run_syn_label)
        run_syn_text = p_syn.add_run(clean_syntax)
        set_font(run_syn_text)
        
        clean_words = s.get('words', '').replace('*', '').replace('#', '')
        if clean_words:
            p_word = doc.add_paragraph(style='List Bullet')
            run_word_label = p_word.add_run("💡 核心词法：")
            run_word_label.bold = True
            run_word_label.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            set_font(run_word_label)
            run_word_text = p_word.add_run(clean_words)
            set_font(run_word_text)

    head2 = doc.add_heading('二、 核心难词与底层逻辑', level=1)
    for run in head2.runs: set_font(run)
    
    vocab_list = analysis_data.get('core_vocabulary', [])
    if vocab_list:
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text, hdr_cells[1].text, hdr_cells[2].text, hdr_cells[3].text = '单词', '音标', '中文释义', '底层记忆法 & 专家例句'
        
        for v in vocab_list:
            row_cells = table.add_row().cells
            row_cells[0].text, row_cells[1].text, row_cells[2].text = v.get('word', ''), v.get('phonetic', ''), v.get('translation', '')
            row_cells[3].text = f"【记忆】{v.get('memory_tip', '').replace('*', '')}\n\n【例句】{v.get('usage_examples', '').replace('*', '')}"
            
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        set_font(run)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ==========================================
# 🧭 导航与主体逻辑
# ==========================================
st.sidebar.markdown("## 🏛️ 教授工作台")
st.sidebar.markdown("---")
page = st.sidebar.radio("核心功能导航：", ["🔍 1. 智能精读教研室", "🗂️ 2. 文章分类档案馆", "🔠 3. 词汇分级记忆库"])

# ------------------------------------------
# 模块 1：智能精读教研室
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
        if not final_text.strip() or final_text.startswith("❌"):
            st.error("请输入有效文本！")
        else:
            with st.spinner("特级教师正在逐句切片，编排语法与词法，请稍候..."):
                system_prompt = "你是一位精通英语语法的特级教师。请将文章逐句彻底拆解。"
                user_prompt = f"""
                必须严格以 JSON 格式输出：
                {{
                    "sentences": [
                        {{
                            "en": "原句英文", "cn": "准确的中文翻译",
                            "syntax": "极简语法拆解（如：主语xx，谓语xx，宾语xx）",
                            "words": "本句核心词及搭配"
                        }}
                    ],
                    "core_vocabulary": [
                        {{
                            "word": "单词", "phonetic": "音标", "translation": "释义", 
                            "memory_tip": "词根词缀", "usage_examples": "造句", "tags": "级别(四级/六级/托福/雅思)"
                        }}
                    ]
                }}
                待分析：\n{final_text}
                """
                try:
                    response = llm_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state['analysis_result'] = json.loads(response.choices[0].message.content)
                    st.session_state['article_content'] = final_text
                    st.rerun() 
                except Exception as e:
                    st.error(f"分析失败: {e}")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        st.divider()
        
        st.markdown("### 📥 导出与归档管理")
        action_col1, action_col2, action_col3 = st.columns([2, 2, 2])
        with action_col1:
            word_file = generate_beautiful_word(res)
            st.download_button("📝 1. 导出精美 Word 教案", data=word_file, file_name="英语逐句精读教案.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with action_col2:
            selected_category = st.selectbox("📂 2. 为本文选择分类：", ["新闻时事", "学术论文", "名著小说", "考试阅读", "日常应用", "未分类"], label_visibility="collapsed")
        with action_col3:
            if st.button("☁️ 3. 同步至云端数据库", use_container_width=True):
                try:
                    formatted_txt = "".join([f"[{i+1}] {s.get('en','')}\n译：{s.get('cn','')}\n语法：{s.get('syntax','')}\n\n" for i, s in enumerate(res.get('sentences', []))])
                    supabase.table('articles').insert({
                        "content": st.session_state['article_content'],
                        "translation": "逐句精读见教案",
                        "teaching_plan": formatted_txt,
                        "category": selected_category
                    }).execute()
                    if res.get('core_vocabulary'):
                        for v in res['core_vocabulary']:
                            supabase.table('vocabulary').insert(v).execute()
                    st.success("✅ 教案及生词已完美分类入库！")
                except Exception as e:
                    st.error(f"保存失败: {e}")

        # ==========================================
        # 🌟 终极压缩版网页预览 (无折叠、高密度、彩色高亮)
        # ==========================================
        st.markdown("### 💻 网页端效果预览")
        for i, s in enumerate(res.get('sentences', [])):
            clean_syntax = s.get('syntax', '').replace('*', '').replace('#', '')
            clean_words = s.get('words', '').replace('*', '').replace('#', '')
            
            # 使用原生 HTML 卡片结构，彻底掌控间距和颜色
            html_block = f"""
            <div style="background-color: #ffffff; border: 1px solid #EAECEF; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-family: 'Times New Roman', serif; font-size: 1.1em; font-weight: bold; color: #111; margin-bottom: 4px; line-height: 1.3;">
                    [{i+1}] {s.get('en', '')}
                </div>
                <div style="font-family: '等线', sans-serif; font-size: 0.95em; color: #555; margin-bottom: 8px; line-height: 1.3;">
                    译：{s.get('cn', '')}
                </div>
                <div style="font-size: 0.9em; color: #222; margin-bottom: 4px; line-height: 1.4;">
                    <span style="color: #1F4E79; font-weight: 600;">🔍 语法：</span>{clean_syntax}
                </div>
                <div style="font-size: 0.9em; color: #222; line-height: 1.4;">
                    <span style="color: #C00000; font-weight: 600;">💡 词法：</span>{clean_words}
                </div>
            </div>
            """
            st.markdown(html_block, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🔠 核心难词深度解析")
        vocab_list = res.get('core_vocabulary', [])
        if vocab_list:
            df_vocab = pd.DataFrame(vocab_list)
            st.dataframe(df_vocab[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
        else:
            st.info("本文较为基础，AI 认为没有必要提取核心难词。")

# ------------------------------------------
# 模块 2：文章分类档案馆
# ------------------------------------------
elif page == "🗂️ 2. 文章分类档案馆":
    st.title("🗂️ 文章分类档案馆")
    try:
        arts_data = supabase.table('articles').select('*').execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data)
            categories = ["全部"] + list(df_arts['category'].dropna().unique()) if 'category' in df_arts.columns else ["全部"]
            cat_filter = st.selectbox("📌 按文章体裁筛选：", categories)
            
            filtered_arts = df_arts[df_arts['category'] == cat_filter].to_dict('records') if cat_filter != "全部" else arts_data
            st.caption(f"当前分类下共有 {len(filtered_arts)} 篇精读教案")
            
            for i, a in enumerate(filtered_arts):
                cat_tag = a.get('category', '未分类')
                with st.expander(f"📖 [{cat_tag}] {a.get('content', '')[:60]}..."):
                    st.text(a.get('teaching_plan', '无'))
        else:
            st.info("尚无文章数据。")
    except Exception as e:
        st.error(f"读取数据失败: {e}")

# ------------------------------------------
# 模块 3：词汇分级记忆库
# ------------------------------------------
elif page == "🔠 3. 词汇分级记忆库":
    st.title("🔠 词汇分级记忆库")
    try:
        vocab_data = supabase.table('vocabulary').select('*').execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data)
            tags = ["全部"] + list(df_vocab['tags'].dropna().unique())
            tag_filter = st.selectbox("🎓 按考试等级/分类筛选：", tags)
            
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            st.metric(label="当前选中单词数", value=len(display_df))
            st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
            
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 导出【{tag_filter}】词汇表 (CSV)", data=csv, file_name=f"{tag_filter}_Vocabulary.csv", mime="text/csv")
        else:
            st.info("尚无词汇数据。")
    except Exception as e:
        st.error(f"读取词汇失败: {e}")