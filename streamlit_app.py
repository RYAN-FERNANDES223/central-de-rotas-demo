"""Demonstração web do projeto de rotas (sem conexão real ao WhatsApp)."""
import shutil
import tempfile
from datetime import date, datetime
from html import escape
import re
from pathlib import Path

import streamlit as st

from banco import conectar, selecionar_banco
from demo_data import PERFIS, enviar, preparar_cenario

st.set_page_config(
    page_title='Central de Rotas | Demonstração',
    page_icon='🚚', layout='wide', initial_sidebar_state='expanded'
)

st.markdown("""
<style>
:root { --verde:#11784f; --verde-escuro:#0b4431; --verde-claro:#eaf7ee;
        --cinza:#667586; --borda:#e5eae9; --fundo:#f7faf8; }
html, body, [data-testid="stAppViewContainer"] {font-family: 'Inter', 'Segoe UI', Arial, sans-serif;}
[data-testid="stAppViewContainer"] {background:#f8faf9;}
.block-container {padding-top:1.3rem!important; padding-bottom:2.4rem!important; max-width:1540px!important;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#ffffff 0%,#f0f9f4 100%); border-right:1px solid #dfece5;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {line-height:1.52;}
.brand {display:flex; align-items:center; gap:12px; margin:5px 0 12px;}
.brand-icon {font-size:30px; background:#e6f5ec; padding:10px; border-radius:14px;}
.brand-title {font-size:1.18rem; color:#102b23; font-weight:800; letter-spacing:-.035em;}
.brand-subtitle {font-size:.77rem; color:#74877e;}
.sidebar-section {font-size:.9rem; font-weight:750; color:#214838; margin:16px 0 7px;}
.stButton>button {border-radius:11px!important; min-height:42px; font-weight:650!important;
                   border-color:#dce9e1; transition:background .15s ease;}
.stButton>button[kind="primary"] {background:#087949!important; border-color:#087949!important; color:white!important;}
.stButton>button:hover {border-color:#0e8955!important;}
[data-testid="stSelectbox"] [data-baseweb="select"]>div {border-radius:11px;}
.top-intro {display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
            margin:0 0 18px; gap:12px;}
.top-intro h1 {font-size:1.85rem; line-height:1.15; margin:0 0 6px; letter-spacing:-.035em; color:#183126;}
.top-intro p {font-size:.95rem; margin:0; color:#68796e;}
.top-pill {background:#e6f5eb; border:1px solid #cce5d4; border-radius:30px; color:#166541;
           padding:8px 12px; font-size:.78rem; font-weight:750; white-space:nowrap;}
.metric-card {min-height:118px; border:1px solid #e0ebe5; border-radius:17px; padding:18px 18px 15px;
              box-shadow:0 3px 13px rgba(30,65,45,.045); display:flex; gap:13px; align-items:flex-start;}
.metric-card.green {background:linear-gradient(120deg,#eaf8ef,#fff);}
.metric-card.blue {background:linear-gradient(120deg,#eaf3ff,#fff);}
.metric-card.amber {background:linear-gradient(120deg,#fff6e4,#fff);}
.metric-card.mint {background:linear-gradient(120deg,#eaf8f1,#fff);}
.metric-icon {font-size:23px; display:flex; align-items:center; justify-content:center; 
              border-radius:14px; background:rgba(255,255,255,.8); height:44px; width:44px; flex:0 0 44px;}
.metric-title {font-size:.86rem; font-weight:700; color:#314c3d;}
.metric-number {font-size:2rem; font-weight:800; line-height:1.25; color:#102b23; font-variant-numeric:tabular-nums;}
.metric-note {font-size:.72rem; color:#7b8981; line-height:1.3;}
.section-heading {color:#193a2a; font-size:1.24rem; font-weight:800; margin:10px 0 2px;}
.section-hint {color:#7a887f; font-size:.82rem; margin:0 0 13px;}
.chat-area {background-color:#f4f3ef; background-image:radial-gradient(#dfe4de 0.7px,transparent 0.7px);
            background-size:22px 22px; border:1px solid #e2e6df; border-radius:16px;
            padding:19px 16px; min-height:370px;}
.message-row {display:flex; margin-bottom:14px;}
.message-row.user {justify-content:flex-end;}
.message-row.bot {justify-content:flex-start;}
.bubble {max-width:84%; padding:11px 14px 9px; border-radius:14px; background:#fff;
         color:#203b2f; font-size:.9rem; line-height:1.5; box-shadow:0 1px 4px rgba(24,44,30,.09);
         overflow-wrap:anywhere;}
.user .bubble {background:#d9f8df; border-bottom-right-radius:4px;}
.bot .bubble {border-bottom-left-radius:4px;}
.bubble-name {font-size:.75rem; font-weight:780; color:#12784b; margin-bottom:4px;}
.message-time {text-align:right; color:#7e9688; margin-top:5px; font-size:.67rem;}
[data-testid="stChatInput"] {border-radius:16px!important; border:1px solid #b9dcca!important;
                              box-shadow:0 2px 9px rgba(19,94,59,.05);}
.route-summary {border:1px solid #e3eae5; background:#fff; border-radius:15px;
                padding:13px 14px; margin-bottom:8px; box-shadow:0 1px 6px rgba(0,0,0,.025);}
.route-head {display:flex; align-items:center; justify-content:space-between; gap:8px;
             flex-wrap:wrap; margin-bottom:8px;}
.route-id {font-size:.75rem; font-weight:800; color:#0b7450; background:#ebf7ee;
           border-radius:7px; padding:4px 7px;}
.route-title {font-size:.95rem; font-weight:760; color:#1d372c; margin:0;}
.route-meta {display:flex; flex-wrap:wrap; gap:7px 15px; font-size:.78rem; color:#67796d; margin:9px 0 4px;}
.status {border-radius:40px; padding:5px 10px; font-size:.74rem; font-weight:700;}
.status-disponivel {background:#def6e6; color:#157340;}
.status-atribuida {background:#e0ecff; color:#215ab1;}
.status-em_andamento {background:#fff0ce; color:#a36b0b;}
.status-concluida {background:#e0f4ee; color:#0c7754;}
.status-cancelada {background:#ffe4e4; color:#b43434;}
.route-driver {color:#1e5b43; font-size:.8rem; margin-top:7px; font-weight:700;}
.info-steps {border:1px solid #dceee3; background:#f4fbf6; border-radius:15px;
             padding:16px; color:#264335; font-size:.88rem; line-height:1.95;}
.role-note {background:#eaf7ef; color:#146243; padding:8px 12px; border-radius:10px;
            font-size:.84rem; margin:5px 0 14px;}
@media (max-width: 850px) {
  .block-container {padding-top:.7rem!important;}
  .metric-card {min-height:104px; padding:12px 10px; gap:7px;}
  .metric-icon {font-size:18px; width:32px; height:32px; flex-basis:32px;}
  .metric-number {font-size:1.5rem;}
  .metric-note {display:none;}
  .bubble {max-width:94%;}
  .top-intro h1 {font-size:1.45rem;}
}
</style>
""", unsafe_allow_html=True)


def inicializar():
    if 'demo_dir' not in st.session_state:
        st.session_state.demo_dir = tempfile.mkdtemp(prefix='rotas_demo_')
    selecionar_banco(Path(st.session_state.demo_dir) / 'rotas_demo.db')
    if 'preparado' not in st.session_state:
        preparar_cenario()
        st.session_state.preparado = True
        st.session_state.perfil = 'Cliente'
        st.session_state.historico = {
            nome: [{'tipo': 'assistant', 'texto':
                'Olá! Esta é uma demonstração do sistema. Envie **oi** ou use os botões abaixo para testar.'}]
            for nome in PERFIS
        }


def reiniciar():
    pasta = st.session_state.get('demo_dir')
    if pasta:
        shutil.rmtree(pasta, ignore_errors=True)
    for campo in ['demo_dir', 'preparado', 'perfil', 'historico']:
        st.session_state.pop(campo, None)
    st.rerun()


def responder(texto):
    perfil = st.session_state.perfil
    resposta = enviar(perfil, texto)
    hora = datetime.now().strftime('%H:%M')
    st.session_state.historico[perfil].extend([
        {'tipo': 'user', 'texto': texto, 'hora': hora},
        {'tipo': 'assistant', 'texto': resposta, 'hora': hora},
    ])


def listar_rotas():
    with conectar() as conn:
        return [dict(r) for r in conn.execute('''
            SELECT r.*, m.nome AS motorista_nome FROM rotas r
            LEFT JOIN motoristas m ON m.id = r.motorista_id
            ORDER BY r.id DESC LIMIT 100
        ''').fetchall()]


def texto_html(valor):
    """Protege entradas digitadas pelo visitante antes de incluí-las no HTML."""
    texto = escape(str(valor))
    texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
    return texto.replace('\n', '<br>')


STATUS = {
    'disponivel': ('Disponível', 'disponivel'),
    'atribuida': ('Atribuída', 'atribuida'),
    'em_andamento': ('Em andamento', 'em_andamento'),
    'concluida': ('Concluída', 'concluida'),
    'cancelada': ('Cancelada', 'cancelada'),
}


def painel_rota(rota):
    """Apresenta os dados reais do banco em um cartão visual (sem alterar regras)."""
    situacao, classe = STATUS.get(rota['status'], (str(rota['status']), 'cancelada'))
    origem = texto_html(rota['origem'])
    destino = texto_html(rota['destino'])
    observacoes = texto_html(rota.get('observacoes') or 'Nenhuma')
    motorista = rota.get('motorista_nome')
    bloco_motorista = (f'<div class="route-driver">🚚 Responsável: {texto_html(motorista)}</div>'
                       if motorista else '')
    try:
        data_exibida = date.fromisoformat(rota['data']).strftime('%d/%m/%Y')
    except ValueError:
        data_exibida = str(rota['data'])
    st.markdown(
        f'<div class="route-summary">'
        f'<div class="route-head"><span class="route-id">#{rota["id"]}</span>'
        f'<span class="status status-{classe}">● {texto_html(situacao)}</span></div>'
        f'<div class="route-title">📍 {origem} → {destino}</div>'
        f'<div class="route-meta"><span>📅 {texto_html(data_exibida)}</span>'
        f'<span>🕘 {texto_html(rota["horario"])}</span></div>'
        f'<div class="route-meta">📦 {observacoes}</div>'
        f'{bloco_motorista}</div>', unsafe_allow_html=True
    )


def painel_conversa(perfil):
    agora_chat = datetime.now().strftime('%H:%M')
    mensagens = []
    for item in st.session_state.historico[perfil][-35:]:
        usuario = item['tipo'] == 'user'
        classe = 'user' if usuario else 'bot'
        rotulo = 'Você' if usuario else '🤖 Assistente de rotas'
        hora = texto_html(item.get('hora', agora_chat))
        mensagens.append(
            f'<div class="message-row {classe}"><div class="bubble">'
            f'<div class="bubble-name">{rotulo}</div>'
            f'<div>{texto_html(item["texto"])}</div>'
            f'<div class="message-time">{hora}{" ✓✓" if usuario else ""}</div>'
            f'</div></div>'
        )
    st.markdown('<div class="chat-area">' + ''.join(mensagens) + '</div>',
                unsafe_allow_html=True)


inicializar()

with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="brand-icon">🚚</span><div>'
        '<div class="brand-title">Central de Rotas</div>'
        '<div class="brand-subtitle">Demonstração comercial · Versão 0.5</div>'
        '</div></div>', unsafe_allow_html=True
    )
    st.info('Ambiente com dados fictícios. Não conectado ao WhatsApp.', icon='ℹ️')
    st.markdown('<div class="sidebar-section">👤 Quem está usando o sistema?</div>',
                unsafe_allow_html=True)
    st.selectbox('Perfil simulado', list(PERFIS), key='perfil',
                 help='Na demonstração é possível trocar de perfil. Na operação real haverá autenticação.')
    st.divider()
    st.markdown('<div class="sidebar-section">📋 Roteiro da apresentação</div>',
                unsafe_allow_html=True)
    st.markdown(
        '① Cliente solicita uma rota  \n'
        '② Motorista A assume o serviço  \n'
        '③ Motorista B verifica a atribuição  \n'
        '④ Administrador acompanha'
    )
    if st.button('🔄 Reiniciar demonstração', use_container_width=True):
        reiniciar()
    st.caption('Os dados são fictícios, temporários e separados por sessão.')

st.markdown(
    '<div class="top-intro"><div>'
    '<h1>Bem-vindo à Central de Rotas!</h1>'
    '<p>Solicitações, motoristas e acompanhamento em um só lugar.</p>'
    '</div><span class="top-pill">● Protótipo navegável · versão 0.5</span></div>',
    unsafe_allow_html=True
)

rotas = listar_rotas()
contagens = {s: sum(r['status']==s for r in rotas)
             for s in ['disponivel', 'atribuida', 'em_andamento', 'concluida']}
resumos = [
    ('📍', 'Disponíveis', contagens['disponivel'], 'Rotas aguardando motorista', 'green'),
    ('👥', 'Atribuídas', contagens['atribuida'], 'Rotas com motorista definido', 'blue'),
    ('🚚', 'Em andamento', contagens['em_andamento'], 'Serviços em execução', 'amber'),
    ('✅', 'Concluídas', contagens['concluida'], 'Serviços finalizados', 'mint'),
]
for coluna, (icone, titulo, total, legenda, cor) in zip(st.columns(4), resumos):
    with coluna:
        st.markdown(
            f'<div class="metric-card {cor}"><div class="metric-icon">{icone}</div>'
            f'<div><div class="metric-title">{titulo}</div>'
            f'<div class="metric-number">{total}</div>'
            f'<div class="metric-note">{legenda}</div></div></div>',
            unsafe_allow_html=True
        )
st.write('')

col_chat, col_visao = st.columns([1.12, 1], gap='large')
with col_chat:
    st.markdown('<div class="section-heading">💬 Simulador de conversa</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="role-note">Perfil selecionado: <strong>{texto_html(st.session_state.perfil)}</strong>'
        ' · Esta conversa simula o WhatsApp.</div>',
        unsafe_allow_html=True
    )
    perfil = st.session_state.perfil
    if perfil == 'Cliente':
        atalhos = [('➕ Nova rota', '/nova'), ('📋 Minhas rotas', '/minhasrotas'), ('✖ Cancelar', '/cancelar')]
    elif perfil.startswith('Motorista'):
        atalhos = [('📋 Ver rotas', '/rotas'), ('🚚 Minhas', '/minhas'), ('ℹ️ Ajuda', '/motorista')]
    else:
        atalhos = [('📊 Resumo', '/resumo'), ('📋 Rotas', '/rotas'), ('⚙️ Ajuda', '/admin')]
    cols = st.columns(len(atalhos))
    for i, (rotulo, comando) in enumerate(atalhos):
        if cols[i].button(rotulo, key=f'atalho_{perfil}_{i}', use_container_width=True):
            responder(comando)
            st.rerun()

    with st.container(height=445, border=False):
        painel_conversa(perfil)

    msg = st.chat_input('Digite uma mensagem como se estivesse no WhatsApp...')
    if msg:
        responder(msg)
        st.rerun()

with col_visao:
    st.markdown('<div class="section-heading">📋 Visão da operação</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-hint">Acompanhe os serviços cadastrados no simulador.</div>',
                unsafe_allow_html=True)
    if perfil == 'Cliente':
        st.info('Experimente **➕ Nova rota** no chat. Após confirmar com **S**, a solicitação aparecerá aqui.', icon='💡')
        st.markdown(
            '<div class="info-steps"><strong>O que o cliente informa</strong><br>'
            '📍 Origem e destino<br>📅 Data e horário<br>'
            '📦 Carga e observações<br>✅ Confirmação do cadastro</div>',
            unsafe_allow_html=True
        )
        st.markdown('#### Rotas desta demonstração')
        for rota in rotas[:8]:
            painel_rota(rota)
    elif perfil.startswith('Motorista'):
        st.markdown('#### Rotas disponíveis')
        disponiveis = [r for r in rotas if r['status']=='disponivel']
        if not disponiveis:
            st.info('Não há rotas disponíveis. Troque para Cliente e cadastre outra.')
        for rota in disponiveis:
            with st.container(border=True):
                painel_rota(rota)
                if st.button('🚚 Aceitar rota', key=f'aceitar_{perfil}_{rota["id"]}',
                             type='primary', use_container_width=True):
                    responder(f"/aceitar {rota['id']}")
                    st.rerun()
        st.markdown('#### Minhas rotas')
        for rota in rotas:
            if rota['motorista_nome'] == perfil:
                with st.container(border=True):
                    painel_rota(rota)
                    if rota['status']=='atribuida':
                        if st.button('▶ Iniciar', key=f'iniciar_{rota["id"]}'):
                            responder(f"/iniciar {rota['id']}")
                            st.rerun()
                    if rota['status'] in ('atribuida','em_andamento'):
                        if st.button('✔ Concluir', key=f'concluir_{rota["id"]}'):
                            responder(f"/concluir {rota['id']}")
                            st.rerun()
    else:
        st.markdown('#### Acompanhamento administrativo')
        if not rotas:
            st.info('Ainda não há solicitações.')
        for rota in rotas:
            with st.container(border=True):
                painel_rota(rota)
                if rota['status']=='atribuida':
                    if st.button('↩ Liberar rota', key=f'liberar_{rota["id"]}'):
                        responder(f"/liberar {rota['id']}")
                        st.rerun()
        st.caption('Cadastre e bloqueie motoristas pelo chat usando /motorista adicionar, /motorista bloquear e /motorista ativar.')

st.divider()
st.caption('⚠️ Demonstração com usuários fictícios, sem autenticação ou conexão ao WhatsApp. Não insira dados pessoais. Armazenamento temporário e isolado por visitante; não é um sistema de produção.')
