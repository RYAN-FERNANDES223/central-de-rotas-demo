"""Demonstração web do projeto de rotas (sem conexão real ao WhatsApp)."""
import shutil
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from banco import conectar, selecionar_banco
from demo_data import PERFIS, enviar, preparar_cenario

st.set_page_config(
    page_title='Central de Rotas | Demonstração',
    page_icon='🚚', layout='wide', initial_sidebar_state='expanded'
)

st.markdown('''
<style>
.block-container {padding-top: 1.5rem; max-width: 1200px;}
[data-testid="stMetric"] {background:#f5faf7; border:1px solid #deede3; padding:15px; border-radius:13px;}
[data-testid="stSidebar"] {background:#f6faf7;}
.hero {background:linear-gradient(120deg,#0b3b2b,#147d55); color:white;
       border-radius:20px; padding:26px 30px; margin-bottom:18px;}
.hero h1 {color:white; font-size:2.15rem; margin:0 0 8px 0;}
.hero p {margin:0; color:#daf3e3; font-size:1.02rem;}
.smallnote {font-size:0.86rem; color:#697b70;}
.demo-tag {display:inline-block; background:#e4f5e9; color:#115e3f;
           border-radius:20px; padding:5px 11px; font-weight:650; font-size:0.8rem;}
</style>
''', unsafe_allow_html=True)


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
    st.session_state.historico[perfil].extend([
        {'tipo': 'user', 'texto': texto},
        {'tipo': 'assistant', 'texto': resposta},
    ])


def listar_rotas():
    with conectar() as conn:
        return [dict(r) for r in conn.execute('''
            SELECT r.*, m.nome AS motorista_nome FROM rotas r
            LEFT JOIN motoristas m ON m.id = r.motorista_id
            ORDER BY r.id DESC LIMIT 100
        ''').fetchall()]


inicializar()

with st.sidebar:
    st.markdown('### 🚚 Central de Rotas')
    st.caption('Demonstração comercial · Versão 0.4')
    st.info('Ambiente de testes com dados fictícios. Não conectado ao WhatsApp.', icon='ℹ️')
    st.markdown('**Escolha quem está usando o sistema:**')
    st.selectbox('Perfil simulado', list(PERFIS), key='perfil',
                 help='Na demonstração você pode trocar livremente de perfil. Na operação real haverá autenticação.')
    st.divider()
    st.markdown('**Roteiro de apresentação**')
    st.markdown('1. Cliente solicita uma rota\n2. Motorista A aceita\n3. Motorista B tenta aceitar a mesma\n4. Administrador acompanha')
    if st.button('🔄 Reiniciar demonstração', use_container_width=True):
        reiniciar()
    st.caption('Os dados ficam isolados por sessão e podem desaparecer ao reiniciar o aplicativo.')

st.markdown('''<div class="hero">
<h1>🚚 Central de Rotas</h1>
<p>Do pedido do cliente à atribuição ao motorista — tudo coordenado pelo bot.</p>
</div>''', unsafe_allow_html=True)
st.markdown('<span class="demo-tag">● Protótipo navegável · sem custo de WhatsApp</span>', unsafe_allow_html=True)
st.write('')

rotas = listar_rotas()
contagens = {s: sum(r['status']==s for r in rotas)
             for s in ['disponivel', 'atribuida', 'em_andamento', 'concluida']}
k1, k2, k3, k4 = st.columns(4)
k1.metric('📍 Disponíveis', contagens['disponivel'])
k2.metric('🚛 Atribuídas', contagens['atribuida'])
k3.metric('🛣️ Em andamento', contagens['em_andamento'])
k4.metric('✅ Concluídas', contagens['concluida'])
st.write('')

col_chat, col_visao = st.columns([1.12, 1], gap='large')
with col_chat:
    st.subheader('💬 Simulador de conversa')
    st.caption(f'Você está simulando: **{st.session_state.perfil}**')
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

    with st.container(height=420, border=True):
        for item in st.session_state.historico[perfil][-35:]:
            with st.chat_message(item['tipo']):
                st.markdown(item['texto'])

    msg = st.chat_input('Digite uma mensagem como se estivesse no WhatsApp...')
    if msg:
        responder(msg)
        st.rerun()

with col_visao:
    st.subheader('📋 Visão da operação')
    st.caption('Ações abaixo alteram os mesmos dados utilizados pelo bot de conversa.')
    if perfil == 'Cliente':
        st.info('Experimente **➕ Nova rota** no chat. Após confirmar com **S**, a solicitação aparecerá aqui.', icon='💡')
        with st.container(border=True):
            st.markdown('#### O que o cliente informa')
            st.markdown('📍 Origem e destino\n\n📅 Data e horário\n\n📦 Carga e observações\n\n✅ Confirmação do cadastro')
        st.markdown('#### Rotas desta demonstração')
        for rota in rotas[:8]:
            with st.container(border=True):
                st.markdown(f"**#{rota['id']} · {rota['origem']} → {rota['destino']}**")
                st.caption(f"{rota['data']} · {rota['horario']} · {rota['status'].replace('_',' ')}")
    elif perfil.startswith('Motorista'):
        st.markdown('#### Rotas disponíveis')
        disponiveis = [r for r in rotas if r['status']=='disponivel']
        if not disponiveis:
            st.info('Não há rotas disponíveis. Troque para Cliente e cadastre outra.')
        for rota in disponiveis:
            with st.container(border=True):
                st.markdown(f"**#{rota['id']} · {rota['origem']} → {rota['destino']}**")
                st.caption(f"📅 {rota['data']} · 🕘 {rota['horario']}")
                st.caption(f"📦 {rota['observacoes'] or 'Sem observações'}")
                if st.button('✅ Aceitar esta rota', key=f'aceitar_{perfil}_{rota["id"]}', use_container_width=True):
                    responder(f"/aceitar {rota['id']}")
                    st.rerun()
        st.markdown('#### Minhas rotas')
        for rota in rotas:
            if rota['motorista_nome'] == perfil:
                with st.container(border=True):
                    st.markdown(f"**#{rota['id']} · {rota['origem']} → {rota['destino']}**")
                    st.caption(f"Situação: {rota['status'].replace('_',' ')}")
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
                st.markdown(f"**#{rota['id']} · {rota['origem']} → {rota['destino']}**")
                st.caption(f"{rota['data']} às {rota['horario']} · {rota['status'].replace('_',' ')}")
                st.write(f"Motorista: **{rota['motorista_nome'] or 'Não atribuído'}**")
                if rota['status']=='atribuida':
                    if st.button('↩ Liberar rota', key=f'liberar_{rota["id"]}'):
                        responder(f"/liberar {rota['id']}")
                        st.rerun()
        st.caption('Cadastre e bloqueie motoristas pelo chat usando /motorista adicionar, /motorista bloquear e /motorista ativar.')

st.divider()
st.caption('⚠️ Demonstração com perfis fictícios, sem autenticação e sem conexão com o WhatsApp. Não use dados reais. Os dados são temporários e separados por visitante; este não é o ambiente de produção.')
