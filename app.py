import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import html
import re
from datetime import datetime, date, timedelta

st.set_page_config(page_title="FlowPulse", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

ARQUIVO_DADOS = "dados_painel.json"
MESES_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS_PT = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def md(texto):
    """Renderiza HTML/Markdown sem linhas em branco ou indentação, que quebram o bloco HTML."""
    limpo_ = "\n".join(l.strip() for l in texto.splitlines() if l.strip())
    st.markdown(limpo_, unsafe_allow_html=True)


def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                d = json.load(f)
                d.setdefault("tarefas", [])
                d.setdefault("anotacoes", [])
                d.setdefault("quick_notes", "")
                return d
        except Exception:
            pass
    return {"tarefas": [], "anotacoes": [], "quick_notes": ""}


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def limpo(txt):  # remove o emoji inicial das categorias/prioridades para exibição
    return txt.split(" ", 1)[-1] if " " in txt else txt


AREAS = ["Trabalho", "Estudos", "Pessoal"]
# Os valores guardados continuam iguais (com emoji) para manter compatibilidade com seus dados atuais.
OPCOES_CAT = {"Trabalho": "💼 Trabalho", "Estudos": "📚 Estudos", "Pessoal": "👤 Pessoal"}
OPCOES_PRIO = ["⚡ Alta", "🟡 Média", "🟢 Baixa"]
COR_AREA = {"Trabalho": "#2563eb", "Estudos": "#7c3aed", "Pessoal": "#0d9488"}
COR_OK, COR_PEND = "#059669", "#94a3b8"


def chip(cat):
    nome = limpo(cat)
    return f"<span class='cat cat-{nome.lower()}'>{nome}</span>"


def nivel_prio(p):
    return "alta" if "Alta" in p else "media" if "Média" in p else "baixa"


def kid(i):  # id seguro para usar em keys
    return str(i).replace(".", "_")


if "db" not in st.session_state:
    st.session_state["db"] = carregar_dados()
db = st.session_state["db"]

# ==============================================================================
# DESIGN SYSTEM  (corporativo, tema claro com lateral azul-marinho)
# Fundo #f3f5f9 | superfície #ffffff | linha #e2e8f0 | texto #0f172a | apoio #64748b
# Destaque #2563eb | ok #059669 | atenção #d97706 | urgente #dc2626 | lateral #0b1426
# Tipografia: Inter
# ==============================================================================
CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f3f5f9; --surface:#ffffff; --surface2:#f8fafc; --line:#e2e8f0;
  --text:#0f172a; --muted:#64748b; --accent:#2563eb; --accent-d:#1d4ed8; --navy:#0b1426;
  --ok:#059669; --warn:#d97706; --bad:#dc2626;
  --shadow:0 1px 2px rgba(15,23,42,.05), 0 1px 3px rgba(15,23,42,.04);
}
html, body, .stApp, .stMarkdown, p, label, input, button, select, textarea, li{
  font-family:'Inter',sans-serif;
}
.stApp{ background:var(--bg)!important; color:var(--text); }
header[data-testid="stHeader"]{ background:transparent!important; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stDeployButton"], .stDeployButton, #MainMenu, footer{ display:none!important; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"]{
  display:flex!important; visibility:visible!important; opacity:1!important; }
[data-testid="stSidebarCollapsedControl"] button, [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"] button{
  background:var(--surface)!important; color:var(--text)!important; border:1px solid var(--line)!important;
  border-radius:8px!important; box-shadow:none!important; }
[data-testid="stSidebarCollapsedControl"] button:hover, [data-testid="stExpandSidebarButton"]:hover, [data-testid="stSidebarCollapseButton"] button:hover{
  border-color:var(--accent)!important; color:var(--accent)!important; }
[data-testid="stSidebarCollapsedControl"] svg, [data-testid="stExpandSidebarButton"] svg, [data-testid="stSidebarCollapseButton"] svg{ fill:currentColor; color:inherit; }
.block-container{ max-width:1180px; padding-top:2rem!important; padding-bottom:4rem; }

h1,h2,h3,h4{ font-family:'Inter',sans-serif!important; font-weight:650!important; letter-spacing:-0.015em; color:var(--text); }
h3{ font-size:1rem!important; padding:0!important; margin:0 0 .4rem 0!important; }
.stCaption, [data-testid="stCaptionContainer"]{ color:var(--muted)!important; }
[data-testid="stWidgetLabel"] p{ color:var(--text); font-weight:500; font-size:.85rem; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{ background:var(--navy)!important; border-right:none; }
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div{ padding-top:1.4rem; }
section[data-testid="stSidebar"] *{ color:#cbd5e1; }
.brand{ display:flex; align-items:center; gap:12px; margin-bottom:1.8rem; padding-bottom:1.4rem; border-bottom:1px solid rgba(255,255,255,.08); }
.brand-mark{ width:36px; height:36px; border-radius:9px; background:var(--accent); display:grid; place-items:center; }
section[data-testid="stSidebar"] .brand-name{ font-size:1.1rem; font-weight:700; color:#ffffff; line-height:1.1; letter-spacing:-0.01em; }
section[data-testid="stSidebar"] .brand-sub{ font-size:.76rem; color:#7c8aa5; }

section[data-testid="stSidebar"] div[role="radiogroup"]{ gap:2px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  padding:.55rem .8rem; border-radius:7px; width:100%; cursor:pointer;
  border-left:3px solid transparent; transition:background .15s;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{ display:none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{ background:rgba(255,255,255,.05); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:rgba(96,165,250,.14); border-left-color:#60a5fa;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{ font-weight:500; font-size:.92rem; color:#cbd5e1; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{ color:#ffffff; font-weight:600; }
section[data-testid="stSidebar"] .side-label{ font-size:.7rem; color:#7c8aa5; margin:1.7rem 0 .4rem 0; text-transform:uppercase; letter-spacing:.09em; font-weight:600; }
section[data-testid="stSidebar"] div[data-baseweb="input"]{ background:rgba(255,255,255,.06)!important; border-color:rgba(255,255,255,.14)!important; }
section[data-testid="stSidebar"] input{ color:#e2e8f0!important; }
.user-box{ margin-top:2.5rem; padding:12px; border:1px solid rgba(255,255,255,.1); border-radius:10px; display:flex; gap:10px; align-items:center; background:rgba(255,255,255,.03); }
.avatar{ width:34px; height:34px; border-radius:50%; background:#1e3a8a; display:grid; place-items:center; font-weight:700; font-size:.8rem; }
section[data-testid="stSidebar"] .avatar{ color:#bfdbfe; }
section[data-testid="stSidebar"] .user-name{ font-weight:600; font-size:.88rem; color:#ffffff; }
section[data-testid="stSidebar"] .user-status{ font-size:.74rem; color:#6ee7b7; }

/* ---------- Topo da página ---------- */
.hero{ display:flex; justify-content:space-between; align-items:center; gap:2rem;
  padding:.2rem 0 1.4rem 0; border-bottom:1px solid var(--line); margin-bottom:1.4rem; }
.hero h1{ font-size:1.85rem!important; line-height:1.15; margin:0!important; padding:0!important; }
.hero-sub{ color:var(--muted); margin-top:.45rem; font-size:.95rem; max-width:60ch; line-height:1.5; }
.ring{ position:relative; width:96px; height:96px; flex:none; }
.ring svg{ transform:rotate(-90deg); }
.ring-num{ position:absolute; inset:0; display:grid; place-items:center; text-align:center;
  font-size:1.3rem; font-weight:700; line-height:1; color:var(--text); }
.ring-num small{ display:block; font-size:.66rem; color:var(--muted); font-weight:500; margin-top:3px; }
.ring circle.fill{ transition:stroke-dashoffset 1s cubic-bezier(.2,.8,.2,1); }

/* ---------- Faixa de números ---------- */
.stats{ display:grid; grid-template-columns:repeat(4,1fr); background:var(--surface);
  border:1px solid var(--line); border-radius:12px; margin-bottom:1.6rem; box-shadow:var(--shadow); }
.stat{ padding:1rem 1.3rem; border-left:1px solid var(--line); }
.stat:first-child{ border-left:none; }
.stat-n{ font-size:1.8rem; font-weight:700; line-height:1.1; font-variant-numeric:tabular-nums; letter-spacing:-0.02em; }
.stat-l{ color:var(--muted); font-size:.8rem; margin-top:3px; font-weight:500; }

/* ---------- Lista de tarefas ---------- */
[class*="st-key-row_"]{ background:var(--surface); border:1px solid var(--line); border-left:4px solid var(--line);
  border-radius:10px; padding:.4rem .9rem; margin-bottom:.5rem; box-shadow:var(--shadow); transition:border-color .15s, background .15s; }
[class*="st-key-row_"]:hover{ background:var(--surface2); }
[class*="st-key-row_alta_"]{ border-left-color:var(--bad); }
[class*="st-key-row_media_"]{ border-left-color:var(--warn); }
[class*="st-key-row_baixa_"]{ border-left-color:var(--ok); }
[class*="st-key-row_feita_"]{ border-left-color:#cbd5e1; opacity:.65; }
.t-title{ font-weight:600; font-size:.94rem; line-height:1.3; padding-top:.2rem; color:var(--text); }
.t-done{ text-decoration:line-through; color:var(--muted); font-weight:500; }
.t-meta{ color:var(--muted); font-size:.78rem; margin-top:4px; display:flex; align-items:center; gap:8px; }
.group-title{ font-size:.74rem; font-weight:700; margin:1.3rem 0 .6rem 0; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
.group-title span{ background:#e2e8f0; color:#475569; font-weight:600; margin-left:.5rem; padding:1px 8px; border-radius:99px; letter-spacing:0; }

/* Botão de excluir discreto */
[class*="st-key-del_"] button{ background:transparent!important; border:none!important; box-shadow:none!important;
  color:#94a3b8!important; min-height:0; padding:.2rem .4rem!important; }
[class*="st-key-del_"] button:hover{ color:var(--bad)!important; background:rgba(220,38,38,.08)!important; }

/* Botões: padrão (secundário) e principal */
.stButton > button{
  background:var(--surface); color:var(--text); border:1px solid var(--line); font-weight:600; font-size:.88rem;
  border-radius:8px; padding:.5rem 1rem; box-shadow:var(--shadow); transition:border-color .15s, color .15s;
}
.stButton > button:hover{ border-color:var(--accent); color:var(--accent); }
.stFormSubmitButton > button, .stButton > button[data-testid="stBaseButton-primary"]{
  background:var(--accent); color:#ffffff; border:1px solid var(--accent); font-weight:600; border-radius:8px;
  padding:.55rem 1.2rem; transition:background .15s;
}
.stFormSubmitButton > button:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover{ background:var(--accent-d); border-color:var(--accent-d); color:#ffffff; }

/* Campos */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{
  background:var(--surface)!important; border-radius:8px!important; border-color:#cbd5e1!important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within{ border-color:var(--accent)!important; }
[data-testid="stExpander"]{ background:var(--surface); border:1px solid var(--line)!important; border-radius:10px; box-shadow:var(--shadow); }
[data-testid="stExpander"] summary{ font-weight:600; }
[data-testid="stExpander"] summary:hover{ color:var(--accent); }
button[data-baseweb="tab"]{ font-weight:600; }

/* Painel lateral: semana */
.week{ display:flex; gap:8px; align-items:flex-end; height:92px; margin:.6rem 0 .2rem 0; }
.wk{ flex:1; text-align:center; font-size:.72rem; color:var(--muted); }
.wk-bar{ background:#e2e8f0; border-radius:5px 5px 3px 3px; height:64px; display:flex; align-items:flex-end; overflow:hidden; margin-bottom:6px; }
.wk-fill{ width:100%; background:var(--accent); border-radius:5px 5px 0 0; }
.wk.hoje .wk-bar{ outline:2px solid var(--navy); outline-offset:1px; }
.wk.hoje{ color:var(--text); font-weight:700; }

/* Dias da semana clicáveis */
[class*="st-key-dia_"] button{ background:var(--surface)!important; color:var(--text)!important; border:1px solid var(--line)!important; width:100%; font-weight:600; padding:.5rem .2rem!important; }
[class*="st-key-dia_"] button:hover{ border-color:var(--accent)!important; color:var(--accent)!important; }
[class*="st-key-diasel_"] button{ background:var(--navy)!important; color:#ffffff!important; border:1px solid var(--navy)!important; width:100%; font-weight:700; padding:.5rem .2rem!important; }
.mini{ background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--line); border-radius:8px; padding:.5rem .6rem; margin-bottom:.4rem; font-size:.8rem; line-height:1.3; box-shadow:var(--shadow); }
.mini.alta{ border-left-color:var(--bad); } .mini.media{ border-left-color:var(--warn); } .mini.baixa{ border-left-color:var(--ok); }
.mini.feita{ opacity:.55; text-decoration:line-through; border-left-color:#cbd5e1; }
.mini small{ display:block; color:var(--muted); margin-top:4px; text-decoration:none; }
.dia-vazio{ color:var(--muted); font-size:.8rem; text-align:center; padding:.8rem 0; }
.dia-count{ color:var(--muted); font-size:.76rem; text-align:center; margin:.3rem 0 .6rem 0; }
[class*="st-key-row_"] [data-testid="stPopover"] button{ background:transparent!important; color:var(--muted)!important; border:none!important; box-shadow:none!important; min-height:0; padding:.2rem .4rem!important; }
[class*="st-key-row_"] [data-testid="stPopover"] button:hover{ color:var(--accent)!important; }

/* Etiquetas */
.cat{ display:inline-block; padding:2px 9px; border-radius:6px; font-size:.7rem; font-weight:600; }
.cat-trabalho{ background:#dbeafe; color:#1d4ed8; }
.cat-estudos{ background:#ede9fe; color:#6d28d9; }
.cat-pessoal{ background:#ccfbf1; color:#0f766e; }
.cat-ideias{ background:#fef3c7; color:#b45309; }
.prio{ display:inline-block; padding:2px 9px; border-radius:6px; font-size:.7rem; font-weight:600; }
.prio-alta{ background:#fee2e2; color:#b91c1c; }
.prio-media{ background:#fef3c7; color:#b45309; }
.prio-baixa{ background:#d1fae5; color:#047857; }

.area-row{ margin-bottom:.9rem; }
.area-top{ display:flex; justify-content:space-between; font-size:.85rem; margin-bottom:5px; font-weight:500; }
.area-top span:last-child{ color:var(--muted); font-weight:400; }
.area-track{ height:7px; background:#e2e8f0; border-radius:99px; overflow:hidden; }
.area-fill{ height:100%; border-radius:99px; }
.panel{ background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:1rem 1.1rem .4rem 1.1rem; box-shadow:var(--shadow); margin-bottom:1rem; }

/* Estado vazio */
.empty{ text-align:center; padding:2.4rem 1rem; border:1px dashed #cbd5e1; border-radius:12px; color:var(--muted); background:var(--surface); }
.empty b{ display:block; color:var(--text); font-size:1rem; margin-bottom:.3rem; }

/* Notas */
.note-body{ line-height:1.65; padding:.2rem 0 .6rem 0; color:var(--text); }

@media (max-width:820px){
  .hero{ flex-direction:column; align-items:flex-start; }
  .stats{ grid-template-columns:repeat(2,1fr); }
  .stat:nth-child(3){ border-left:none; }
  .stat:nth-child(n+3){ border-top:1px solid var(--line); }
}
@media (prefers-reduced-motion:reduce){ *{ transition:none!important; animation:none!important; } }
</style>
"""
md(re.sub(r"/\*.*?\*/", "", CSS, flags=re.S))

st.session_state.setdefault("data_sel", date.today())


def ir_para(d, pagina=None):
    st.session_state["data_sel"] = d
    if pagina:
        st.session_state["menu"] = pagina


def mudar_semana(dias):
    st.session_state["data_sel"] = st.session_state["data_sel"] + timedelta(days=dias)


def semana_de(d):
    ini = d - timedelta(days=d.weekday())
    return [ini + timedelta(days=i) for i in range(7)]


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    md("""
    <div class="brand"><div class="brand-mark"><svg width="19" height="19" viewBox="0 0 24 24" fill="#ffffff"><path d="M13 2 4 14h6l-1 8 9-12h-6z"/></svg></div>
      <div><div class="brand-name">FlowPulse</div><div class="brand-sub">Gestão de tarefas e rotina</div></div></div>
    """)

    menu = st.radio("Navegação", ["Hoje", "Semana", "Evolução", "Notas"], key="menu", label_visibility="collapsed")

    md("<div class='side-label'>Data</div>")
    data_selecionada = st.date_input("Data", key="data_sel", label_visibility="collapsed", format="DD/MM/YYYY")
    data_str = data_selecionada.strftime("%Y-%m-%d")
    dia_pt = f"{data_selecionada.day} de {MESES_PT[data_selecionada.month - 1]} de {data_selecionada.year}"

    md("<div class='side-label'>Filtrar por área</div>")
    area = st.radio("Área", ["Todas"] + AREAS, key="area", label_visibility="collapsed")

    md("""
    <div class="user-box"><div class="avatar">IF</div>
      <div><div class="user-name">Ingrid Ferreira</div>
      <div class="user-status">● Salvo neste computador</div></div></div>
    """)

df_geral = pd.DataFrame(db["tarefas"])
if df_geral.empty:
    df_geral = pd.DataFrame(columns=["id", "data", "titulo", "categoria", "concluida", "prioridade"])
elif "prioridade" not in df_geral.columns:
    df_geral["prioridade"] = "🟡 Média"


df_todas = df_geral.copy()
if area != "Todas":
    df_geral = df_geral[df_geral["categoria"].map(limpo) == area]


def hero(titulo, sub, ring_pct=None):
    ring = ""
    if ring_pct is not None:
        c = 2 * 3.14159 * 40
        off = c * (1 - ring_pct / 100)
        ring = f"""<div class="ring"><svg width="96" height="96" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r="40" fill="none" stroke="#e2e8f0" stroke-width="8"/>
          <circle class="fill" cx="48" cy="48" r="40" fill="none" stroke="#059669" stroke-width="8"
            stroke-linecap="round" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}"/></svg>
          <div class="ring-num"><div>{ring_pct}%<small>do dia</small></div></div></div>"""
    md(f"""<div class="hero"><div><h1>{titulo}</h1><div class="hero-sub">{sub}</div></div>{ring}</div>""")


def atualizar(tid, **campos):
    for t in db["tarefas"]:
        if t["id"] == tid:
            t.update(campos)
    salvar_dados(db)


def excluir(tid):
    db["tarefas"] = [t for t in db["tarefas"] if t["id"] != tid]
    salvar_dados(db)


def linha_tarefa(row, feita):
    chave = kid(row["id"])
    nivel = nivel_prio(row["prioridade"])
    prio = "feita" if feita else nivel
    with st.container(key=f"row_{prio}_{chave}"):
        c1, c2, c3, c4 = st.columns([0.07, 0.66, 0.17, 0.1], vertical_alignment="center")
        with c1:
            marcado = st.checkbox("concluir", value=feita, key=f"chk_{chave}", label_visibility="collapsed")
        with c2:
            t = html.escape(row["titulo"])
            meta = f"{chip(row['categoria'])}<span class='prio prio-{nivel}'>Prioridade {limpo(row['prioridade']).lower()}</span>"
            cls = "t-title t-done" if feita else "t-title"
            md(f"<div class='{cls}'>{t}</div><div class='t-meta'>{meta}</div>")
        with c3:
            with st.popover(":material/event: Data", use_container_width=True):
                nd = st.date_input("Mover para", value=datetime.strptime(row["data"], "%Y-%m-%d").date(),
                                   key=f"nd_{chave}", format="DD/MM/YYYY")
                if st.button("Mover tarefa", key=f"mv_{chave}", type="primary", use_container_width=True):
                    atualizar(row["id"], data=nd.strftime("%Y-%m-%d"))
                    st.toast(f"Tarefa movida para {nd.strftime('%d/%m')}", icon=":material/event:")
                    st.rerun()
        with c4:
            if st.button(":material/close:", key=f"del_{chave}", help="Excluir tarefa"):
                excluir(row["id"])
                st.rerun()
        if marcado != feita:
            atualizar(row["id"], concluida=marcado)
            st.rerun()


# ==============================================================================
# HOJE
# ==============================================================================
if menu == "Hoje":
    df_dia = df_geral[df_geral["data"] == data_str]
    total = len(df_dia)
    feitas = int(df_dia["concluida"].sum()) if total else 0
    abertas = total - feitas
    pct = int(feitas / total * 100) if total else 0

    h = datetime.now().hour
    saudacao = "Bom dia" if h < 12 else "Boa tarde" if h < 18 else "Boa noite"
    if total == 0:
        sub = f"{dia_pt}. Nada planejado ainda — comece adicionando a primeira tarefa."
    elif abertas == 0:
        sub = f"{dia_pt}. Todas as tarefas foram concluídas."
    else:
        sub = f"{dia_pt}. Restam {abertas} de {total} tarefas."
    hero(f"{saudacao}, Ingrid", sub, pct)

    cols_sem = st.columns(7)
    for col, d in zip(cols_sem, semana_de(data_selecionada)):
        n = len(df_geral[df_geral["data"] == d.strftime("%Y-%m-%d")])
        rotulo = f"{DIAS_PT[d.weekday()]} {d.day}" + (f" ({n})" if n else "")
        pref = "diasel" if d == data_selecionada else "dia"
        col.button(rotulo, key=f"{pref}_faixa_{d.isoformat()}", on_click=ir_para, args=(d,), use_container_width=True)
    st.write("")

    md(f"""
    <div class="stats">
      <div class="stat"><div class="stat-n">{total}</div><div class="stat-l">Planejadas</div></div>
      <div class="stat"><div class="stat-n" style="color:var(--ok)">{feitas}</div><div class="stat-l">Concluídas</div></div>
      <div class="stat"><div class="stat-n" style="color:var(--warn)">{abertas}</div><div class="stat-l">Em aberto</div></div>
      <div class="stat"><div class="stat-n" style="color:var(--accent)">{pct}%</div><div class="stat-l">Progresso</div></div>
    </div>""")

    with st.expander("Adicionar tarefa", expanded=(total == 0)):
        with st.form("form_add_task", clear_on_submit=True):
            titulo_tarefa = st.text_input("Descrição da tarefa", placeholder="Ex: Estudar módulo 3 de Python")
            f1, f2, f3 = st.columns(3)
            categoria = f1.selectbox("Categoria", list(OPCOES_CAT.values()), format_func=limpo,
                                     index=AREAS.index(area) if area in AREAS else 0)
            prioridade = f2.selectbox("Prioridade", OPCOES_PRIO, format_func=limpo, index=1)
            data_tarefa = f3.date_input("Data de realização", value=data_selecionada, format="DD/MM/YYYY")
            if st.form_submit_button("Adicionar tarefa", use_container_width=True) and titulo_tarefa.strip():
                db["tarefas"].append({
                    "id": datetime.now().timestamp(), "data": data_tarefa.strftime("%Y-%m-%d"), "titulo": titulo_tarefa.strip(),
                    "categoria": categoria, "prioridade": prioridade, "concluida": False})
                salvar_dados(db)
                st.toast(f"Tarefa agendada para {data_tarefa.strftime('%d/%m/%Y')}", icon=":material/check_circle:")
                st.rerun()

    col_main, col_side = st.columns([1.7, 1], gap="large")

    with col_main:
        if df_dia.empty:
            md("<div class='empty'><b>Nenhuma tarefa neste dia</b>Use “Adicionar tarefa” para planejar o dia.</div>")
        else:
            ordem = {"Alta": 0, "Média": 1, "Baixa": 2}
            pend = df_dia[df_dia["concluida"] == False].copy()
            pend["_o"] = pend["prioridade"].map(lambda p: next((v for k, v in ordem.items() if k in p), 1))
            pend = pend.sort_values("_o")
            conc = df_dia[df_dia["concluida"] == True]

            if not pend.empty:
                md(f"<div class='group-title'>A fazer<span>{len(pend)}</span></div>")
                for _, r in pend.iterrows():
                    linha_tarefa(r, False)
            if not conc.empty:
                md(f"<div class='group-title'>Concluídas<span>{len(conc)}</span></div>")
                for _, r in conc.iterrows():
                    linha_tarefa(r, True)

    with col_side:
        md("### Progresso por área")
        dd = df_todas[df_todas["data"] == data_str]
        linhas = ""
        for a in AREAS:
            sub_a = dd[dd["categoria"].map(limpo) == a]
            t_a, f_a = len(sub_a), (int(sub_a["concluida"].sum()) if len(sub_a) else 0)
            p_a = int(f_a / t_a * 100) if t_a else 0
            linhas += (f"<div class='area-row'><div class='area-top'><span>{a}</span><span>{f_a}/{t_a} concluídas</span></div>"
                       f"<div class='area-track'><div class='area-fill' style='width:{p_a}%;background:{COR_AREA[a]}'></div></div></div>")
        md(f"<div class='panel'>{linhas}</div>")

        md("### Últimos 7 dias")
        barras = ""
        for i in range(6, -1, -1):
            d = data_selecionada - timedelta(days=i)
            sub_df = df_geral[df_geral["data"] == d.strftime("%Y-%m-%d")]
            p = int(sub_df["concluida"].sum() / len(sub_df) * 100) if len(sub_df) else 0
            barras += (f"<div class='wk {'hoje' if i == 0 else ''}'><div class='wk-bar'>"
                       f"<div class='wk-fill' style='height:{p}%'></div></div>{DIAS_PT[d.weekday()]}</div>")
        md(f"<div class='panel'><div class='week'>{barras}</div></div>")
        st.caption("Altura da barra = % de tarefas concluídas no dia.")

        st.write("")
        md("### Rascunho")
        st.caption("Links, lembretes e ideias soltas.")
        rascunho = st.text_area("Rascunho", value=db.get("quick_notes", ""), height=170,
                                placeholder="Cole aqui um link, uma ideia ou um lembrete...",
                                label_visibility="collapsed")
        if st.button("Salvar rascunho", type="primary", use_container_width=True):
            db["quick_notes"] = rascunho
            salvar_dados(db)
            st.toast("Rascunho salvo", icon=":material/save:")

# ==============================================================================
# SEMANA
# ==============================================================================
elif menu == "Semana":
    dias = semana_de(data_selecionada)
    ini, fim = dias[0], dias[-1]
    periodo = f"{ini.day} {MESES_PT[ini.month - 1][:3].lower()} a {fim.day} {MESES_PT[fim.month - 1][:3].lower()} de {fim.year}"
    hero("Semana", f"{periodo}. Clique em um dia para abrir e gerenciar as tarefas dele.")

    n1, n2, n3 = st.columns([1, 1, 1])
    n1.button("Semana anterior", key="sem_ant", on_click=mudar_semana, args=(-7,), use_container_width=True)
    n2.button("Esta semana", key="sem_hoje", on_click=ir_para, args=(date.today(),), use_container_width=True)
    n3.button("Próxima semana", key="sem_prox", on_click=mudar_semana, args=(7,), use_container_width=True)
    st.write("")

    cols = st.columns(7, gap="small")
    for col, d in zip(cols, dias):
        d_str = d.strftime("%Y-%m-%d")
        tarefas_dia = df_geral[df_geral["data"] == d_str]
        with col:
            pref = "diasel" if d == data_selecionada else "dia"
            st.button(f"{DIAS_PT[d.weekday()]} {d.day}", key=f"{pref}_sem_{d.isoformat()}",
                      on_click=ir_para, args=(d, "Hoje"), use_container_width=True)
            feitas_d = int(tarefas_dia["concluida"].sum()) if len(tarefas_dia) else 0
            md(f"<div class='dia-count'>{feitas_d}/{len(tarefas_dia)} concluídas</div>" if len(tarefas_dia)
               else "<div class='dia-count'>livre</div>")
            for _, r in tarefas_dia.iterrows():
                cls = "feita" if r["concluida"] else nivel_prio(r["prioridade"])
                md(f"<div class='mini {cls}'>{html.escape(r['titulo'])}<small>{chip(r['categoria'])}</small></div>")

# ==============================================================================
# EVOLUÇÃO
# ==============================================================================
elif menu == "Evolução":
    hero("Evolução", "Trabalho, estudos e vida pessoal analisados separadamente. O filtro de área da lateral não afeta esta tela.")

    LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  font=dict(color="#334155", family="Inter, sans-serif"), margin=dict(t=10, b=10, l=10, r=10))
    MAPA_STATUS = {"Concluídas": COR_OK, "Pendentes": COR_PEND}

    def painel(df, nome=None):
        if df.empty:
            md(f"<div class='empty'><b>Sem tarefas{' de ' + nome.lower() if nome else ''} ainda</b>Adicione tarefas em “Hoje” para ver os gráficos.</div>")
            return
        tot, conc = len(df), int(df["concluida"].sum())
        taxa = int(conc / tot * 100)
        md(f"""
        <div class="stats" style="grid-template-columns:repeat(4,1fr)">
          <div class="stat"><div class="stat-n">{tot}</div><div class="stat-l">Tarefas registradas</div></div>
          <div class="stat"><div class="stat-n" style="color:var(--ok)">{conc}</div><div class="stat-l">Concluídas</div></div>
          <div class="stat"><div class="stat-n" style="color:var(--warn)">{tot - conc}</div><div class="stat-l">Pendentes</div></div>
          <div class="stat"><div class="stat-n" style="color:var(--accent)">{taxa}%</div><div class="stat-l">Taxa de conclusão</div></div>
        </div>""")
        g1, g2 = st.columns(2, gap="large")
        with g1:
            if nome is None:
                md("### Tarefas por área")
                dn = df["area"].value_counts().reset_index()
                dn.columns = ["Área", "Qtd"]
                fig = px.pie(dn, values="Qtd", names="Área", hole=0.62, color="Área", color_discrete_map=COR_AREA)
            else:
                md("### Concluídas e pendentes")
                dn = pd.DataFrame({"Status": ["Concluídas", "Pendentes"], "Qtd": [conc, tot - conc]})
                fig = px.pie(dn, values="Qtd", names="Status", hole=0.62, color="Status", color_discrete_map=MAPA_STATUS)
            fig.update_layout(**LAYOUT, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", title=""))
            fig.update_traces(marker=dict(line=dict(color="#f3f5f9", width=3)), textinfo="value")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            md("### Tarefas por dia")
            if nome is None:
                dh = df.groupby(["data", "area"]).size().reset_index(name="Qtd")
                fig = px.bar(dh, x="data", y="Qtd", color="area", barmode="stack", color_discrete_map=COR_AREA)
            else:
                dh = df.assign(Status=df["concluida"].map({True: "Concluídas", False: "Pendentes"})) \
                       .groupby(["data", "Status"]).size().reset_index(name="Qtd")
                fig = px.bar(dh, x="data", y="Qtd", color="Status", barmode="stack", color_discrete_map=MAPA_STATUS)
            fig.update_layout(**LAYOUT, xaxis=dict(showgrid=False, title=""), yaxis=dict(gridcolor="#e2e8f0", title="", dtick=1),
                              legend=dict(orientation="h", y=1.1, x=1, xanchor="right", title=""))
            fig.update_traces(marker=dict(cornerradius=5))
            st.plotly_chart(fig, use_container_width=True)
        if nome is None:
            md("### Taxa de conclusão por área")
            tx = df.groupby("area")["concluida"].mean().mul(100).round().reset_index()
            tx.columns = ["Área", "Taxa"]
            fig = px.bar(tx, x="Taxa", y="Área", orientation="h", color="Área", color_discrete_map=COR_AREA, text="Taxa")
            fig.update_layout(**LAYOUT, height=200, showlegend=False, xaxis=dict(range=[0, 100], gridcolor="#e2e8f0", title="%"),
                              yaxis=dict(title=""))
            fig.update_traces(marker=dict(cornerradius=5), texttemplate="%{text}%")
            st.plotly_chart(fig, use_container_width=True)

    if df_todas.empty:
        md("<div class='empty'><b>Ainda não há histórico</b>Adicione tarefas em “Hoje” para ver os gráficos.</div>")
    else:
        df_e = df_todas.copy()
        df_e["area"] = df_e["categoria"].map(limpo)
        abas = st.tabs(["Visão geral"] + AREAS)
        with abas[0]:
            painel(df_e)
        for aba, nome in zip(abas[1:], AREAS):
            with aba:
                painel(df_e[df_e["area"] == nome], nome)

# ==============================================================================
# NOTAS
# ==============================================================================
else:
    hero("Notas", "Atas de reunião, resumos de estudo e ideias para consultar depois.")

    with st.expander("Nova nota", expanded=False):
        with st.form("form_nota", clear_on_submit=True):
            n1, n2 = st.columns([2.5, 1])
            titulo_n = n1.text_input("Título", placeholder="Ex: Alinhamento sobre a API do n8n")
            categoria_n = n2.selectbox("Categoria", ["💼 Trabalho", "📚 Estudos", "💡 Ideias e projetos"], format_func=limpo)
            conteudo_n = st.text_area("Conteúdo", height=140, placeholder="Escreva os pontos importantes...")
            if st.form_submit_button("Salvar nota", use_container_width=True) and titulo_n.strip() and conteudo_n.strip():
                db["anotacoes"].append({
                    "id": datetime.now().timestamp(), "data": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                    "titulo": titulo_n.strip(), "categoria": categoria_n, "conteudo": conteudo_n.strip()})
                salvar_dados(db)
                st.toast("Nota salva", icon=":material/check_circle:")
                st.rerun()

    st.write("")
    notas = db["anotacoes"]
    if not notas:
        md("<div class='empty'><b>Nenhuma nota ainda</b>Crie a primeira em “Nova nota”.</div>")
    else:
        busca = st.text_input("Buscar", placeholder="Buscar por título ou conteúdo", label_visibility="collapsed")
        for n in reversed(notas):
            if busca and busca.lower() not in (n["titulo"] + n["conteudo"]).lower():
                continue
            with st.expander(f"{n['titulo']}  —  {limpo(n['categoria'])}, {n['data']}"):
                md(f"<div class='note-body'>{html.escape(n['conteudo']).replace(chr(10), '<br>')}</div>")
                with st.container(key=f"del_n_{kid(n['id'])}"):
                    if st.button("Excluir nota", key=f"btn_n_{kid(n['id'])}"):
                        db["anotacoes"] = [x for x in db["anotacoes"] if x["id"] != n["id"]]
                        salvar_dados(db)
                        st.rerun()