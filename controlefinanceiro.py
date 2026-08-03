import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import requests

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# --- Configurações do Banco de Dados Supabase (via API REST) ---
SUPABASE_URL = "https://metlyrhdjzsjmhxazzpm.supabase.co"
SUPABASE_KEY = "sb_publishable_b1qRwHNc9NOM_OG7TTAitA_IljT8dJ-"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

ENDPOINT = f"{SUPABASE_URL}/rest/v1/dados_financeiros"

# Estilização CSS para Alinhamento Perfeito e Espaçamento Justinho
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.15rem !important;
    }
    .element-container {
        margin-bottom: 0px !important;
    }
    .stExpander {
        margin-bottom: 0px !important;
        border-radius: 4px !important;
    }
    .stExpander > div:first-child {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        min-height: 2.1rem !important;
    }
    div[data-testid="stCheckbox"] {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        min-height: 2.1rem !important;
    }
    div[data-testid="stButton"] > button {
        padding: 0.1rem 0.4rem !important;
        min-height: 2.1rem !important;
        height: 2.1rem !important;
        margin: 0px !important;
    }
    hr {
        margin-top: 0.2rem !important;
        margin-bottom: 0.4rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. Sistema de Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Acesso Restrito")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if usuario == "Gabriel" and senha == "Gsa250619":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")
    st.stop()

# --- Funções Auxiliares de Data ---
def add_months(date_str, num_months):
    y, m = map(int, date_str.split('-'))
    m += num_months
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"

def diff_months(date_str1, date_str2):
    y1, m1 = map(int, date_str1.split('-'))
    y2, m2 = map(int, date_str2.split('-'))
    return (y1 - y2) * 12 + (m1 - m2)

def get_month_name(date_str):
    meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    y, m = map(int, date_str.split('-'))
    return f"{meses[m]} {y}"

# --- 2. Sistema de Salvar/Carregar Dados no SUPABASE (via REST API) ---
def carregar_dados():
    try:
        url = f"{ENDPOINT}?id=eq.principal&select=conteudo"
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            dados = res.json()
            if dados and len(dados) > 0:
                return dados[0].get("conteudo", {})
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
    return None

def salvar_dados(silencioso=False):
    dados = {
        "salario_fixo": st.session_state.salario_fixo,
        "rendas_extras": st.session_state.rendas_extras,
        "contas_fixas": st.session_state.contas_fixas,
        "pagamentos_fixas": st.session_state.pagamentos_fixas,
        "pagamentos_cartoes": st.session_state.get("pagamentos_cartoes", {}),
        "cartoes": st.session_state.cartoes,
        "compras_cartao": st.session_state.compras_cartao,
        "antecipacoes": st.session_state.get("antecipacoes", {})
    }
    
    payload = [{
        "id": "principal",
        "conteudo": dados
    }]
    
    try:
        res = requests.post(ENDPOINT, json=payload, headers=HEADERS)
        if res.status_code in [200, 201] and not silencioso:
            st.toast('Progresso salvo no Supabase com sucesso!', icon='✅')
    except Exception as e:
        st.error(f"Erro ao salvar no Supabase: {e}")

# --- Inicialização do Session State ---
if 'dados_iniciados' not in st.session_state:
    dados_salvos = carregar_dados()
    if dados_salvos:
        st.session_state.salario_fixo = dados_salvos.get("salario_fixo", 0.0)
        st.session_state.rendas_extras = dados_salvos.get("rendas_extras", [])
        st.session_state.contas_fixas = dados_salvos.get("contas_fixas", [])
        st.session_state.pagamentos_fixas = dados_salvos.get("pagamentos_fixas", {})
        st.session_state.pagamentos_cartoes = dados_salvos.get("pagamentos_cartoes", {})
        st.session_state.cartoes = dados_salvos.get("cartoes", [{"id": "c1", "nome": "Cartão Dia 5"}, {"id": "c2", "nome": "Cartão Dia 20"}])
        st.session_state.compras_cartao = dados_salvos.get("compras_cartao", [])
        st.session_state.antecipacoes = dados_salvos.get("antecipacoes", {})
    else:
        st.session_state.salario_fixo = 0.0
        st.session_state.rendas_extras = []
        st.session_state.contas_fixas = []
        st.session_state.pagamentos_fixas = {}
        st.session_state.pagamentos_cartoes = {}
        st.session_state.cartoes = [
            {"id": "c1", "nome": "Cartão Dia 5"},
            {"id": "c2", "nome": "Cartão Dia 20"}
        ]
        st.session_state.compras_cartao = []
        st.session_state.antecipacoes = {}
        
    hoje = datetime.now()
    st.session_state.mes_view = f"{hoje.year:04d}-{hoje.month:02d}"
    st.session_state.dados_iniciados = True

mes_view = st.session_state.mes_view

# --- BARRA LATERAL (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    
    with st.expander("➕ Adicionar Nova Conta/Dívida", expanded=True):
        opcoes_destino = ["🏠 Contas Fixas"] + [f"💳 {c['nome']}" for c in st.session_state.cartoes]
        destino_selecionado = st.selectbox("Selecione o Destino", opcoes_destino)
        
        with st.form("form_add_geral", clear_on_submit=True):
            desc_item = st.text_input("Descrição (Ex: Mercado, Aluguel)")
            val_item = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0)
            
            is_cartao = destino_selecionado != "🏠 Contas Fixas"
            
            if is_cartao:
                is_recorrente = st.checkbox("Gasto Recorrente (Fixo todo mês)")
                parc_item = st.number_input("Parcelas", min_value=1, step=1, value=1, disabled=is_recorrente)
            else:
                is_recorrente = False
                parc_item = 1
                
            btn_add = st.form_submit_button("Lançar Conta")
            
            if btn_add and desc_item and val_item > 0:
                if not is_cartao:
                    st.session_state.contas_fixas.append({
                        "id": str(uuid.uuid4()),
                        "desc": desc_item,
                        "valor": val_item
                    })
                else:
                    nome_cartao_limpo = destino_selecionado.replace("💳 ", "")
                    cartao_obj = next((c for c in st.session_state.cartoes if c['nome'] == nome_cartao_limpo), None)
                    
                    if cartao_obj:
                        st.session_state.compras_cartao.append({
                            "id": str(uuid.uuid4()),
                            "cartao_id": cartao_obj["id"],
                            "desc": desc_item,
                            "valor_total": val_item,
                            "parcelas": 1 if is_recorrente else parc_item,
                            "recorrente": is_recorrente,
                            "mes_inicio": mes_view
                        })
                salvar_dados(silencioso=True)
                st.rerun()

    with st.expander("💵 Minhas Rendas", expanded=False):
        st.subheader("Salário Fixo")
        novo_salario = st.number_input("Salário Mensal (R$)", min_value=0.0, value=float(st.session_state.salario_fixo), step=100.0)
        if novo_salario != st.session_state.salario_fixo:
            st.session_state.salario_fixo = novo_salario
            salvar_dados(silencioso=True)
            st.rerun()

        st.divider()
        st.subheader("Rendas Extras do Mês")
        with st.form("form_renda_extra", clear_on_submit=True):
            desc_renda = st.text_input("Descrição (Ex: Freela)")
            val_renda = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
            btn_add_renda = st.form_submit_button("Adicionar Renda")
            if btn_add_renda and desc_renda and val_renda > 0:
                st.session_state.rendas_extras.append({"id": str(uuid.uuid4()), "mes": mes_view, "desc": desc_renda, "valor": val_renda})
                salvar_dados(silencioso=True)
                st.rerun()

        rendas_mes = [r for r in st.session_state.rendas_extras if r['mes'] == mes_view]
        for renda in rendas_mes:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{renda['desc']}**: R$ {renda['valor']:.2f}")
            if c2.button("❌", key=f"del_renda_{renda['id']}"):
                st.session_state.rendas_extras = [r for r in st.session_state.rendas_extras if r['id'] != renda['id']]
                salvar_dados(silencioso=True)
                st.rerun()

    with st.expander("💳 Configurar Cartões", expanded=False):
        with st.form("form_novo_cartao", clear_on_submit=True):
            novo_nome_cartao = st.text_input("Nome do Cartão (ex: Cartão Dia 10)")
            btn_add_cartao = st.form_submit_button("Criar Cartão")
            if btn_add_cartao and novo_nome_cartao:
                st.session_state.cartoes.append({"id": str(uuid.uuid4()), "nome": novo_nome_cartao})
                salvar_dados(silencioso=True)
                st.rerun()

# --- Lógica de Filtro e Cálculos ---
rendas_mes = [r for r in st.session_state.rendas_extras if r['mes'] == mes_view]
total_receitas = st.session_state.salario_fixo + sum(r['valor'] for r in rendas_mes)

total_fixas = sum(c['valor'] for c in st.session_state.contas_fixas)
total_fixas_pagas = sum(c['valor'] for c in st.session_state.contas_fixas if st.session_state.pagamentos_fixas.get(f"{mes_view}_{c['id']}", False))

despesas_cartao_mes = []
for compra in st.session_state.compras_cartao:
    diferenca_meses = diff_months(mes_view, compra.get('mes_inicio', mes_view))
    is_rec = compra.get('recorrente', False)
    
    qtd_antecipadas = st.session_state.antecipacoes.get(compra['id'], 0)
    
    if is_rec:
        if diferenca_meses >= 0:
            despesas_cartao_mes.append({
                'id': compra['id'],
                'cartao_id': compra['cartao_id'],
                'desc': compra['desc'],
                'valor_total': compra['valor_total'],
                'valor_parcela': compra['valor_total'],
                'parcela_atual': 1,
                'total_parcelas': 1,
                'recorrente': True
            })
    else:
        parcelas_qtd = compra.get('parcelas', 1) - qtd_antecipadas
        if 0 <= diferenca_meses < parcelas_qtd:
            valor_parcela = compra['valor_total'] / compra.get('parcelas', 1)
            despesas_cartao_mes.append({
                'id': compra['id'],
                'cartao_id': compra['cartao_id'],
                'desc': compra['desc'],
                'valor_total': compra['valor_total'],
                'valor_parcela': valor_parcela,
                'parcela_atual': diferenca_meses + 1,
                'total_parcelas': parcelas_qtd,
                'recorrente': False
            })

# Cálculo de faturas pagas
total_cartoes = sum(d['valor_parcela'] for d in despesas_cartao_mes)
total_cartoes_pagos = 0.0

for c in st.session_state.cartoes:
    if st.session_state.pagamentos_cartoes.get(f"{mes_view}_{c['id']}", False):
        desps_c = [d['valor_parcela'] for d in despesas_cartao_mes if d['cartao_id'] == c['id']]
        total_cartoes_pagos += sum(desps_c)

total_despesas_geral = total_fixas + total_cartoes
total_pagos_geral = total_fixas_pagas + total_cartoes_pagos
despesas_pendentes_geral = total_despesas_geral - total_pagos_geral
saldo_projetado = total_receitas - total_despesas_geral

# --- TELA PRINCIPAL ---

col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("💸 Meu Controle Financeiro")
with col_head2:
    st.write("") 
    if st.button("💾 Salvar Progresso", use_container_width=True, type="primary"):
        salvar_dados()

col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    if st.button("⬅️ Mês Anterior", use_container_width=True):
        st.session_state.mes_view = add_months(st.session_state.mes_view, -1)
        st.rerun()
with col_nav2:
    st.markdown(f"<h2 style='text-align: center; margin-top: 0;'>📅 {get_month_name(st.session_state.mes_view)}</h2>", unsafe_allow_html=True)
with col_nav3:
    if st.button("Próximo Mês ➡️", use_container_width=True):
        st.session_state.mes_view = add_months(st.session_state.mes_view, 1)
        st.rerun()

st.divider()

col_res1, col_res2, col_res3, col_res4 = st.columns(4)
col_res1.metric("💰 Receitas Totais", f"R$ {total_receitas:.2f}")
col_res2.metric("📉 Despesas Pendentes", f"R$ {despesas_pendentes_geral:.2f}", delta=f"- R$ {total_pagos_geral:.2f} pagas", delta_color="inverse")
col_res3.metric("✅ Contas Pagas (Mês)", f"R$ {total_pagos_geral:.2f}")
col_res4.metric("💲 Saldo Projetado Livre", f"R$ {saldo_projetado:.2f}")

st.divider()

st.header("🛒 Visualização de Contas do Mês")

num_cols = 1 + len(st.session_state.cartoes)
cols_despesas = st.columns(num_cols)

# ---> Coluna 1: Contas Fixas <---
with cols_despesas[0]:
    st.subheader("🏠 Contas Fixas")
    
    with st.expander("📌 Informações"):
        st.write("Contas fixas se repetem todos os meses.")

    st.markdown("---")

    with st.expander("📋 Ver Gastos Fixos", expanded=True):
        for conta in st.session_state.contas_fixas:
            c_chk, c_del = st.columns([5, 1])
            chave_pagamento = f"{mes_view}_{conta['id']}"
            
            is_pago = st.session_state.pagamentos_fixas.get(chave_pagamento, False)
            novo_status = c_chk.checkbox(f"{conta['desc']} (R$ {conta['valor']:.2f})", value=is_pago, key=f"chk_{chave_pagamento}")
            
            if novo_status != is_pago:
                st.session_state.pagamentos_fixas[chave_pagamento] = novo_status
                salvar_dados(silencioso=True)
                st.rerun()
                
            if c_del.button("❌", key=f"del_fixa_{conta['id']}", help="Excluir conta de todos os meses"):
                st.session_state.contas_fixas = [c for c in st.session_state.contas_fixas if c['id'] != conta['id']]
                salvar_dados(silencioso=True)
                st.rerun()
                
    st.markdown(f"**Total Fixas: R$ {total_fixas:.2f}**")

# ---> Colunas 2+: Cartões <---
for idx, cartao in enumerate(st.session_state.cartoes):
    with cols_despesas[idx + 1]:
        chave_pago_cartao = f"{mes_view}_{cartao['id']}"
        is_cartao_pago = st.session_state.pagamentos_cartoes.get(chave_pago_cartao, False)
        
        novo_status_cartao = st.checkbox(f"💳 **{cartao['nome']}**", value=is_cartao_pago, key=f"chk_cartao_{chave_pago_cartao}")
        if novo_status_cartao != is_cartao_pago:
            st.session_state.pagamentos_cartoes[chave_pago_cartao] = novo_status_cartao
            salvar_dados(silencioso=True)
            st.rerun()
        
        with st.expander("⚙️ Opções do Cartão"):
            novo_nome = st.text_input("Editar Nome:", value=cartao["nome"], key=f"edit_nome_{cartao['id']}")
            if novo_nome != cartao["nome"]:
                st.session_state.cartoes[idx]["nome"] = novo_nome
                salvar_dados(silencioso=True)

            tem_dividas = any(c['cartao_id'] == cartao['id'] for c in st.session_state.compras_cartao)
            if not tem_dividas:
                if st.button("🗑️ Excluir Cartão", key=f"del_cartao_{cartao['id']}"):
                    st.session_state.cartoes.pop(idx)
                    salvar_dados(silencioso=True)
                    st.rerun()

        st.markdown("---")

        despesas_deste_cartao_neste_mes = [d for d in despesas_cartao_mes if d['cartao_id'] == cartao['id']]
        
        with st.expander(f"📋 Ver Gastos ({cartao['nome']})", expanded=True):
            for desp in despesas_deste_cartao_neste_mes:
                if desp['recorrente']:
                    texto_parcela = " (Fixo)"
                elif desp['total_parcelas'] > 1:
                    texto_parcela = f" ({desp['parcela_atual']}/{desp['total_parcelas']})"
                else:
                    texto_parcela = ""

                c_edit, c_del = st.columns([5, 1])
                
                with c_edit:
                    with st.expander(f"✏️ {desp['desc']}{texto_parcela} - R$ {desp['valor_parcela']:.2f}"):
                        compra_original = next((c for c in st.session_state.compras_cartao if c['id'] == desp['id']), None)
                        
                        if compra_original and not desp['recorrente'] and desp['total_parcelas'] > 1:
                            st.caption("⚡ Opção de Antecipação:")
                            if st.button(f"🚀 Antecipar +1 Parcela no Mês Atual", key=f"antecipa_{desp['id']}"):
                                st.session_state.antecipacoes[desp['id']] = st.session_state.antecipacoes.get(desp['id'], 0) + 1
                                salvar_dados(silencioso=True)
                                st.toast("1 Parcela antecipada e quitada do futuro!", icon="🚀")
                                st.rerun()
                            st.divider()

                        with st.form(f"form_edit_compra_{desp['id']}"):
                            novo_desc = st.text_input("Editar Descrição", value=desp['desc'])
                            
                            val_atual_total = compra_original['valor_total'] if compra_original else desp['valor_total']
                            parc_atual_total = compra_original['parcelas'] if compra_original else desp['total_parcelas']
                            rec_atual = compra_original.get('recorrente', False) if compra_original else desp['recorrente']
                            
                            novo_valor_total = st.number_input("Editar Valor Total (R$)", min_value=0.0, value=float(val_atual_total), step=10.0)
                            novo_rec = st.checkbox("Recorrente (Fixo todo mês)", value=rec_atual, key=f"rec_{desp['id']}")
                            nova_qtd_parc = st.number_input("Editar Qtd Parcelas", min_value=1, step=1, value=int(parc_atual_total), disabled=novo_rec, key=f"parc_{desp['id']}")
                            
                            btn_salvar_edicao = st.form_submit_button("Salvar Alterações")
                            if btn_salvar_edicao and compra_original:
                                compra_original['desc'] = novo_desc
                                compra_original['valor_total'] = novo_valor_total
                                compra_original['recorrente'] = novo_rec
                                compra_original['parcelas'] = 1 if novo_rec else nova_qtd_parc
                                salvar_dados(silencioso=True)
                                st.rerun()

                with c_del:
                    if st.button("❌", key=f"del_desp_{desp['id']}"):
                        st.session_state.compras_cartao = [c for c in st.session_state.compras_cartao if c['id'] != desp['id']]
                        salvar_dados(silencioso=True)
                        st.rerun()

        total_cartao = sum(d['valor_parcela'] for d in despesas_deste_cartao_neste_mes)
        st.markdown(f"**Total Mês: R$ {total_cartao:.2f}**")

st.divider()

# --- Seção 3: Exportar para WhatsApp ---
st.header("📱 Exportar Resumo do Mês (Cartões)")
st.caption("Clique no ícone de 'Copiar' no canto superior direito da caixa abaixo para enviar no WhatsApp.")

texto_export = ""

for cartao in st.session_state.cartoes:
    despesas_deste = [d for d in despesas_cartao_mes if d['cartao_id'] == cartao['id']]
    
    if despesas_deste:
        texto_export += f"*{cartao['nome']}:*\n"
        total_deste = sum(d['valor_parcela'] for d in despesas_deste)
        
        for d in despesas_deste:
            if not d['recorrente'] and d['total_parcelas'] > 1:
                tag_parc = f" ({d['parcela_atual']}/{d['total_parcelas']})"
            else:
                tag_parc = ""
                
            texto_export += f"o   {d['desc']}{tag_parc}: R${d['valor_parcela']:.2f}\n".replace('.', ',')
            
        texto_export += f"\nTotal {cartao['nome']}: R${total_deste:.2f}\n\n".replace('.', ',')

if not texto_export.strip():
    st.code("Nenhum cartão possui despesas registradas para este mês.", language="text")
else:
    st.code(texto_export.strip(), language="text")
