import streamlit as st
import json
import pandas as pd
import trafilatura
import io
import datetime
import random
import string
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from openai import OpenAI
from supabase import create_client, Client

# ==========================================
# ⚙️ 核心配置区
# ==========================================


llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 🎨 UI/UX 顶级视觉系统
# ==========================================
st.set_page_config(page_title="顶级英语教研平台-商业版", page_icon="🏛️", layout="wide")

custom_css = """
<style>
    .stApp { background-color: #FAFAFC; }
    h1, h2, h3, h4, h5 { font-family: 'Times New Roman', 'DengXian', '等线', serif !important; color: #1A1A24; font-weight: bold;}
    section[data-testid="stSidebar"] { min-width: 220px !important; max-width: 220px !important; background-color: #111118 !important; border-right: 1px solid #2D2D3B; }
    section[data-testid="stSidebar"] h2 { font-family: 'Times New Roman', 'DengXian', '等线', serif !important; color: #FFFFFF !important; font-size: 1.1em !important; text-align: center; margin-top: -30px; margin-bottom: 20px; }
    section[data-testid="stSidebar"] .stAlert p { color: #8892B0 !important; font-size: 0.8em; }
    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: transparent !important; padding: 8px 12px !important; border-radius: 6px !important; margin: 0 !important; transition: all 0.2s ease; border: none !important; cursor: pointer; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p { color: #8892B0 !important; font-size: 0.85em !important; font-family: 'DengXian', '等线', sans-serif !important; margin: 0; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: #202535 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p { color: #F0F0F5 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { background-color: #1a1e2a !important; border-left: 3px solid #00B4D8 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p { color: #FFFFFF !important; font-weight: bold !important; }
    section[data-testid="stMain"] div[role="radiogroup"] { gap: 2px !important; }
    section[data-testid="stMain"] div[role="radiogroup"] > label { background-color: transparent !important; border: none !important; border-radius: 6px !important; padding: 8px 10px !important; transition: all 0.2s; }
    section[data-testid="stMain"] div[role="radiogroup"] > label p { font-size: 0.85em !important; color: #555; margin: 0;}
    section[data-testid="stMain"] div[role="radiogroup"] > label:hover { background-color: #EAECEF !important; }
    section[data-testid="stMain"] div[role="radiogroup"] > label[data-checked="true"] { background-color: #E2E6EA !important; border-left: 3px solid #1F4E79 !important; border-radius: 4px !important; }
    section[data-testid="stMain"] div[role="radiogroup"] > label[data-checked="true"] p { font-weight: bold !important; color: #111 !important;}
    div.stButton > button { border-radius: 6px !important; font-weight: 600 !important; border: none !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease; }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🛠️ 核心工具函数区 (Word 全息导出引擎)
# ==========================================
def set_font(run, ascii_font='Times New Roman', east_asia_font='等线'): 
    run.font.name = ascii_font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)

def generate_beautiful_word(analysis_data, full_text=""):
    doc = Document()
    
    # 🌿 注入护眼底色 (豆沙绿 F4F6F1)
    try:
        bg = parse_xml(f'<w:background {nsdecls("w")} w:color="F4F6F1"/>')
        doc.settings.element.insert(0, bg)
        shape = parse_xml(f'<w:displayBackgroundShape {nsdecls("w")}/>')
        doc.settings.element.append(shape)
    except Exception:
        pass # 如果 XML 注入失败则忽略

    # 设置全局默认字体
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    
    # 缩小主标题
    h1 = doc.add_heading('📖 英语专家级精读教案', level=1)
    for run in h1.runs: set_font(run)

    # 1. 注入英文原文
    if full_text:
        h2_org = doc.add_heading('一、 英文原文', level=2)
        for run in h2_org.runs: set_font(run)
        
        p_org = doc.add_paragraph()
        run_org = p_org.add_run(full_text.strip())
        run_org.font.size = Pt(11)
        run_org.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        set_font(run_org)
        doc.add_paragraph() # 加空行

    # 2. 注入逐句拆解
    h2_syn = doc.add_heading('二、 逐句语法与词法拆解', level=2)
    for run in h2_syn.runs: set_font(run)

    for i, s in enumerate(analysis_data.get('sentences', [])):
        # 英文原句 (大字体)
        p_en = doc.add_paragraph()
        run_en = p_en.add_run(f"[{i+1}] {s.get('en', '')}")
        run_en.bold = True
        run_en.font.size = Pt(12)
        set_font(run_en)
        
        # 中文翻译 (小字体)
        p_cn = doc.add_paragraph()
        run_cn = p_cn.add_run(f"译文：{s.get('cn', '')}")
        run_cn.font.size = Pt(10.5)
        run_cn.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        set_font(run_cn)
        
        # 语法解析 (小字体)
        p_syn = doc.add_paragraph()
        r_l1 = p_syn.add_run("🔍 语法：")
        r_l1.bold, r_l1.font.color.rgb, r_l1.font.size = True, RGBColor(0x1F, 0x4E, 0x79), Pt(10.5)
        set_font(r_l1)
        r_t1 = p_syn.add_run(s.get('syntax', '').replace('*', ''))
        r_t1.font.size = Pt(10.5)
        set_font(r_t1)
        
        # 词法解析 (小字体)
        if s.get('words'): 
            p_w = doc.add_paragraph()
            r_l2 = p_w.add_run("💡 词法：")
            r_l2.bold, r_l2.font.color.rgb, r_l2.font.size = True, RGBColor(0xC0, 0x00, 0x00), Pt(10.5)
            set_font(r_l2)
            r_t2 = p_w.add_run(s.get('words', '').replace('*', ''))
            r_t2.font.size = Pt(10.5)
            set_font(r_t2)
            
        # 句与句之间加一个极小的间距
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 3. 注入核心词汇表
    v_list = analysis_data.get('core_vocabulary', [])
    if v_list:
        doc.add_paragraph() # 空行
        h2_voc = doc.add_heading('三、 核心词汇表', level=2)
        for run in h2_voc.runs: set_font(run)
        
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        for i, h in enumerate(['单词', '音标', '释义', '逻辑与例句']): 
            r_th = table.rows[0].cells[i].paragraphs[0].add_run(h)
            r_th.bold = True
            set_font(r_th)
            
        for v in v_list:
            row = table.add_row().cells
            row[0].text, row[1].text, row[2].text = v.get('word',''), v.get('phonetic',''), v.get('translation','')
            row[3].text = f"【记忆】{v.get('memory_tip','')}\n【例句】{v.get('usage_examples','')}"
            
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs: 
                        r.font.size = Pt(10) # 表格内使用更小的字体
                        set_font(r)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def fetch_text_smart(url): 
    try: 
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded) if downloaded else "⚠️ 未能识别正文"
    except Exception: return "抓取异常"


# ==========================================
# 🔐 商业版认证系统
# ==========================================
if 'user' not in st.session_state: st.session_state['user'] = None

if st.session_state['user'] is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🏛️ 顶级英语精读工作台</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>专业教研 · 深度分析 · 邀请制商业版</p>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1, 1, 1])
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 账号登录", "🎟️ 凭邀请码注册"])
        with tab_login:
            login_email = st.text_input("邮箱地址", key="l_email")
            login_pwd = st.text_input("登录密码", type="password", key="l_pwd")
            if st.button("立即验证并进入", use_container_width=True, type="primary"):
                try: 
                    response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                    st.session_state['user'] = response.user; st.rerun()
                except Exception: st.error("账号或密码有误。")
        with tab_signup:
            signup_email = st.text_input("设置登录邮箱", key="s_email"); signup_pwd = st.text_input("设置密码 (>6位)", type="password", key="s_pwd"); signup_code = st.text_input("🔑 专属邀请码")
            if st.button("核销邀请码并注册", use_container_width=True):
                if not signup_email or len(signup_pwd) < 6 or not signup_code: st.warning("请完整填写。")
                else:
                    with st.spinner("核验..."):
                        code_res = supabase.table('invitation_codes').select('*').eq('code', signup_code).eq('is_used', False).execute()
                        if not code_res.data: st.error("邀请码无效。")
                        else:
                            try:
                                supabase.auth.sign_up({"email": signup_email, "password": signup_pwd})
                                duration = code_res.data[0]['duration_days']; exp_date = (datetime.datetime.now() + datetime.timedelta(days=duration)).isoformat()
                                supabase.table('invitation_codes').update({'is_used': True}).eq('code', signup_code).execute()
                                supabase.table('subscriptions').insert({'user_email': signup_email, 'expires_at': exp_date}).execute()
                                st.success("✅ 注册成功！请切换登录。")
                            except Exception: st.error("注册失败。")
    st.stop()

USER_EMAIL = st.session_state['user'].email
IS_ADMIN = (USER_EMAIL == ADMIN_EMAIL)
CURRENT_USER_ID = st.session_state['user'].id

if not IS_ADMIN:
    sub_res = supabase.table('subscriptions').select('*').eq('user_email', USER_EMAIL).execute()
    if not sub_res.data or datetime.datetime.now() > datetime.datetime.fromisoformat(sub_res.data[0]['expires_at']):
        st.error("账号已到期。"); 
        if st.button("退出"): st.session_state['user'] = None; st.rerun()
        st.stop()

# ==========================================
# 🧭 大师级侧边栏导航
# ==========================================
st.sidebar.markdown("## 🏛️ 工作台")
menu_options = ["🔍 智能精读教研室", "🗂️ 文章分类档案馆", "🔠 词汇分级记忆库"]
if IS_ADMIN: menu_options.append("👑 老板发卡中心")

page = st.sidebar.radio("核心导航：", menu_options, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption(f"👤 账号: {USER_EMAIL}")
if st.sidebar.button("🚪 退出系统", use_container_width=True): st.session_state['user'] = None; st.rerun()

# ==========================================
# 👑 路由分发区 
# ==========================================
if IS_ADMIN and page == "👑 老板发卡中心":
    st.title("👑 发卡中心")
    with st.form("gen_code_form"):
        plan = st.radio("时长：", ["30天", "90天", "365天"], horizontal=True)
        days_map = {"30天": 30, "90天": 90, "365天": 365}
        if st.form_submit_button("🔨 生成激活码", type="primary"):
            new_code = f"VIP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            try:
                supabase.table('invitation_codes').insert({"code": new_code, "duration_days": days_map[plan], "is_used": False}).execute()
                st.success(f"成功: {new_code}"); st.code(new_code)
            except Exception: st.error("失败")

elif page == "🔍 智能精读教研室":
    st.title("🔍 智能精读教研室")
    col1, col2 = st.columns([3, 1])
    with col1: url = st.text_input("🔗 输入英文文章链接：")
    with col2: 
        st.write(""); st.write("")
        if st.button("🛰️ 提取正文", use_container_width=True):
            if url: st.session_state['temp_text'] = fetch_text_smart(url)
    
    final_text = st.text_area("📝 待分析文本：", value=st.session_state.get('temp_text', ""), height=150)
    if st.button("🧠 生成教案", type="primary"):
        if not final_text.strip(): st.error("请输入文本")
        else:
            with st.spinner("AI正在切片..."):
                prompt = f"""以JSON格式输出全句拆解：{{"sentences": [{{"en": "原句英文", "cn": "翻译", "syntax": "极简语法", "words": "核心词法"}}], "core_vocabulary": [{{"word": "单词", "phonetic": "音标", "translation": "释义", "memory_tip": "记忆法", "usage_examples": "造句", "tags": "级别"}}]}} 待分析：\n{final_text}""" 
                try:
                    res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                    st.session_state['analysis_result'] = json.loads(res.choices[0].message.content); st.session_state['article_content'] = final_text; st.rerun()
                except Exception: st.error("分析失败")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']; st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.download_button("📝 导出 Word", data=generate_beautiful_word(res, st.session_state.get('article_content', '')), file_name="教案.docx", use_container_width=True)
        with c2: cat = st.selectbox("📂 分类：", ["新闻时事", "学术论文", "名著小说", "考试阅读", "日常应用", "未分类"], label_visibility="collapsed")
        with c3:
            if st.button("☁️ 同步云端", use_container_width=True):
                txt = "".join([f"[{i+1}] {s.get('en','')}\n译：{s.get('cn','')}\n🔍 语法：{s.get('syntax','').replace('*', '')}\n💡 词法：{s.get('words','').replace('*', '')}\n\n" for i,s in enumerate(res.get('sentences', []))])
                # ⚠️ 核心修复：把完整 JSON 打包进 translation 字段
                try:
                    supabase.table('articles').insert({"user_id": CURRENT_USER_ID, "content": st.session_state['article_content'], "teaching_plan": txt, "translation": json.dumps(res), "category": cat}).execute()
                    for v in res.get('core_vocabulary', []): v["user_id"] = CURRENT_USER_ID; supabase.table('vocabulary').insert(v).execute()
                    st.success("✅ 保存成功")
                except Exception as e: st.error(f"保存失败: {e}")
                    
        for i, s in enumerate(res.get('sentences', [])):
            st.markdown(f"""<div style='background:#F4F6F1; border-radius:8px; padding:12px; margin-bottom:8px;'>
                <div style='font-family: Times New Roman; font-size:1.05em; font-weight:bold;'>[{i+1}] {s.get('en','')}</div><div style='color:#555; font-size:0.95em;'>译：{s.get('cn','')}</div>
                <div style='font-size:0.9em; margin-top:4px;'><span style='color:#1F4E79;'>🔍 语法：</span>{s.get('syntax','')}</div><div style='font-size:0.9em;'><span style='color:#C00000;'>💡 词法：</span>{s.get('words','')}</div></div>""", unsafe_allow_html=True)
        if res.get('core_vocabulary'): st.dataframe(pd.DataFrame(res['core_vocabulary'])[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)

# ==========================================
# 🗂️ 档案馆 (全息重建导出)
# ==========================================
elif page == "🗂️ 文章分类档案馆":
    st.title("🗂️ 私人档案馆")
    try:
        arts_data = supabase.table('articles').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data)
            categories = ["全部"] + list(df_arts['category'].dropna().unique()) if 'category' in df_arts.columns else ["全部"]
            tabs = st.tabs(categories)
            
            for i, tab in enumerate(tabs):
                with tab:
                    cat_filter = categories[i]
                    filtered_arts = [a for a in arts_data if a.get('category') == cat_filter] if cat_filter != "全部" else arts_data
                    
                    if filtered_arts:
                        col_list, col_content = st.columns([1, 3.5], gap="large")
                        
                        with col_list:
                            st.markdown("##### 📑 归档列表")
                            options = [f"{idx+1}. {a.get('content', '')[:30]}..." for idx, a in enumerate(filtered_arts)]
                            selected_title = st.radio("选择文章", options, key=f"radio_{i}", label_visibility="collapsed")
                        
                        with col_content:
                            selected_art = filtered_arts[options.index(selected_title)]
                            art_id = selected_art.get('id')
                            
                            # ⚠️ 核心修复：尝试读取暗藏的 JSON 全息数据
                            raw_json_str = selected_art.get('translation', '')
                            try:
                                full_analysis_data = json.loads(raw_json_str) if raw_json_str else None
                            except:
                                full_analysis_data = None
                            
                            act_col1, act_col2 = st.columns(2)
                            with act_col1: 
                                # 如果有全息数据，就生成完美带单词的 Word
                                if full_analysis_data:
                                    word_data = generate_beautiful_word(full_analysis_data, selected_art.get('content', ''))
                                else:
                                    # 兼容老数据：如果没有暗藏的 JSON，就勉强导出一个只有文本的版本
                                    st.caption("提示：旧文章可能不包含完整单词表")
                                    word_data = export_plain_text_to_word(selected_art.get('teaching_plan', ''))
                                    
                                st.download_button("📥 完美重建导出 (Word)", data=word_data, file_name="归档教案.docx", use_container_width=True, key=f"dl_{art_id}_{i}")
                                
                            with act_col2: 
                                if st.button("🗑️ 永久删除", key=f"del_{art_id}_{i}", use_container_width=True):
                                    supabase.table('articles').delete().eq('id', art_id).execute(); st.rerun()
                                    
                            eye_care_bg = "#F3F6F0"
                            st.markdown("##### 📰 英文原文 (Original Text)")
                            st.markdown(f"""<div style='background-color: {eye_care_bg}; padding: 12px 16px; border-radius: 6px; font-family: "Times New Roman", serif; font-size: 0.9em; color: #444; max-height: 120px; overflow-y: auto; margin-bottom: 15px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);'>
                                {selected_art.get('content', '无原文记录')}
                            </div>""", unsafe_allow_html=True)
                            
                            st.markdown("##### 🔬 逐句解析 (Compact Analysis)")
                            st.markdown(f"""<div style='background-color: {eye_care_bg}; padding: 16px; border-radius: 6px; font-family: "Times New Roman", "DengXian", sans-serif; font-size: 0.9em; line-height: 1.5; color: #222; white-space: pre-wrap; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);'>
{selected_art.get('teaching_plan', '暂无记录').strip()}
                            </div>""", unsafe_allow_html=True)
                    else: st.info("暂无文章。")
        else: st.info("空空如也。")
    except Exception as e: pass

elif page == "🔠 词汇分级记忆库":
    st.title("🔠 私人词汇库")
    try:
        vocab_data = supabase.table('vocabulary').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data); tag_filter = st.selectbox("🎓 筛选：", ["全部"] + list(df_vocab['tags'].dropna().unique()))
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            st.metric("生词量", len(display_df)); st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
        else: st.info("无词汇。")
    except Exception: pass