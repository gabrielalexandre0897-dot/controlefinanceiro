import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

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
    st.stop() # Para a execução do app aqui se não estiver logado

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

# --- 2. Sistema de Salvar/Carregar Dados ---
DATA_FILE = "meus_dados_financeiros.json"

def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def salvar_dados():
    dados = {
        "salario_fixo": st.session_state.salario_fixo,
        "rendas_extras": st.session_state.rendas_extras,
        "contas_fixas": st.session_state.contas_fixas,
        "pagamentos_fixas": st.session_state.pagamentos_fixas,
        "cartoes": st.session_state.cartoes,
        "compras_cartao": st.session_state.compras_cartao
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- Inicialização do Session State (Com carregamento) ---
if 'dados_iniciados' not in st.session_state:
    dados_salvos = carregar_dados()
    if dados_salvos:
        st.session_state.salario_fixo = dados_salvos.get("salario_fixo", 0.0)
        st.session_state.rendas_extras = dados_salvos.get("rendas_extras", [])
        st.session_state.contas_fixas = dados_salvos.get("contas_fixas", [])
        st.session_state.pagamentos_fixas = dados_salvos.get("pagamentos_fixas", {})
        st.session_state.cartoes = dados_salvos.get("cartoes", [{"id": "c1", "nome": "Cartão Dia 5"}, {"id": "c2", "nome": "Cartão Dia 20"}])
        st.session_state.compras_cartao = dados_salvos.get("compras_cartao", [])
    else:
        st.session_state.salario_fixo = 0.0
        st.session_state.rendas_extras = []
        st.session_state.contas_fixas = []
        st.session_state.pagamentos_fixas = {}
        st.session_state.cartoes = [
            {"id": "c1", "nome": "Cartão Dia 5"},
            {"id": "c2", "nome": "Cartão Dia 20"}
        ]
        st.session_state.compras_cartao = []
        
    hoje = datetime.now()
    st.session_state.mes_view = f"{hoje.year:04d}-{hoje.month:02d}"
    st.session_state.dados_iniciados = True

mes_view = st.session_state.mes_view

# --- Lógica de Filtro e Cálculos do Mês Selecionado ---
# 1. Rendas (Salário fixo agora é global)
rendas_mes = [r for r in st.session_state.rendas_extras if r['mes'] == mes_view]
total_receitas = st.session_state.salario_fixo + sum(r['valor'] for r in rendas_mes)

# 2. Contas Fixas e Pagamentos
total_fixas = sum(c['valor'] for c in st.session_state.contas_fixas)
total_fixas_pagas = sum(c['valor'] for c in st.session_state.contas_fixas if st.session_state.pagamentos_fixas.get(f"{mes_view}_{c['id']}", False))
total_fixas_pendentes = total_fixas - total_fixas_pagas

# 3. Despesas de Cartão
despesas_cartao_mes = []
for compra in st.session_state.compras_cartao:
    diferenca_meses = diff_months(mes_view, compra['mes_inicio'])
    if 0 <= diferenca_meses < compra['parcelas']:
        valor_parcela = compra['valor_total'] / compra['parcelas']
        despesas_cartao_mes.append({
            'id': compra['id'],
            'cartao_id': compra['cartao_id'],
            'desc': compra['desc'],
            'valor_parcela': valor_parcela,
            'parcela_atual': diferenca_meses + 1,
            'total_parcelas': compra['parcelas']
        })

total_cartoes = sum(d['valor_parcela'] for d in despesas_cartao_mes)

# --- Métricas Finais ---
total_despesas_geral = total_fixas + total_cartoes
despesas_pendentes_geral = total_fixas_pendentes + total_cartoes
saldo_projetado = total_receitas - total_despesas_geral

# --- Cabeçalho e Navegação ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("💸 Meu Controle Financeiro")
with col_head2:
    st.write("") # Espaçamento
    if st.button("💾 Salvar Progresso", use_container_width=True, type="primary"):
        salvar_dados()
        st.toast('Progresso salvo com sucesso!', icon='✅')

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

# --- Painel de Resumo ---
col_res1, col_res2, col_res3, col_res4 = st.columns(4)
col_res1.metric("💰 Receitas Totais", f"R$ {total_receitas:.2f}")
col_res2.metric("📉 Despesas Pendentes", f"R$ {despesas_pendentes_geral:.2f}", delta=f"- R$ {total_fixas_pagas:.2f} pagas", delta_color="inverse")
col_res3.metric("✅ Contas Pagas (Mês)", f"R$ {total_fixas_pagas:.2f}")
col_res4.metric("💲 Saldo Projetado Livre", f"R$ {saldo_projetado:.2f}")

st.write("") 

# --- Seção 1: Entradas (Ocultável) ---
with st.expander("💵 Minhas Rendas (Clique para expandir/ocultar)", expanded=False):
    col_renda1, col_renda2 = st.columns(2)
    with col_renda1:
        st.subheader("Salário Fixo (Todos os meses)")
        novo_salario = st.number_input("Valor do Salário (R$)", min_value=0.0, value=float(st.session_state.salario_fixo), step=100.0)
        if novo_salario != st.session_state.salario_fixo:
            st.session_state.salario_fixo = novo_salario
            st.rerun()

    with col_renda2:
        st.subheader("Rendas Extras do Mês")
        with st.form("form_renda_extra", clear_on_submit=True):
            cols = st.columns([2, 1, 1])
            desc_renda = cols[0].text_input("Descrição (Ex: Freela)")
            val_renda = cols[1].number_input("Valor (R$)", min_value=0.0, step=50.0)
            btn_add_renda = cols[2].form_submit_button("Adicionar")
            if btn_add_renda and desc_renda and val_renda > 0:
                st.session_state.rendas_extras.append({"id": str(uuid.uuid4()), "mes": mes_view, "desc": desc_renda, "valor": val_renda})
                st.rerun()

        for renda in rendas_mes:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{renda['desc']}**: R$ {renda['valor']:.2f}")
            if c2.button("❌", key=f"del_renda_{renda['id']}"):
                st.session_state.rendas_extras = [r for r in st.session_state.rendas_extras if r['id'] != renda['id আলোচন']
                st.rerun()

st.divider()

# --- Seção 2: Despesas (Contas Fixas e Cartões) ---
st.header("🛒 Minhas Contas e Cartões")

with st.expander("➕ Gerenciar Cartões (Adicionar novo cartão)"):
    with st.form("form_novo_cartao", clear_on_submit=True):
        novo_nome_cartao = st.text_input("Nome do Cartão (ex: Cartão Dia 10)")
        btn_add_cartao = st.form_submit_button("Criar Cartão")
        if btn_add_cartao and novo_nome_cartao:
            st.session_state.cartoes.append({"id": str(uuid.uuid4()), "nome": novo_nome_cartao})
            st.rerun()

num_cols = 1 + len(st.session_state.cartoes)
cols_despesas = st.columns(num_cols)

# ---> Coluna 1: Contas Fixas <---
with cols_despesas[0]:
    st.subheader("🏠 Contas Fixas")
    
    with st.form("form_fixas", clear_on_submit=True):
        desc_fixa = st.text_input("Nova Conta Fixa")
        val_fixa = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        btn_add_fixa = st.form_submit_button("Adicionar")
        if btn_add_fixa and desc_fixa and val_fixa > 0:
            st.session_state.contas_fixas.append({"id": str(uuid.uuid4()), "desc": desc_fixa, "valor": val_fixa})
            st.rerun()

    for conta in st.session_state.contas_fixas:
        c_chk, c_del = st.columns([4, 1])
        chave_pagamento = f"{mes_view}_{conta['id']}"
        
        is_pago = st.session_state.pagamentos_fixas.get(chave_pagamento, False)
        novo_status = c_chk.checkbox(f"{conta['desc']} (R$ {conta['valor']:.2f})", value=is_pago, key=f"chk_{chave_pagamento}")
        
        if novo_status != is_pago:
            st.session_state.pagamentos_fixas[chave_pagamento] = novo_status
            st.rerun()
            
        if c_del.button("❌", key=f"del_fixa_{conta['id']}", help="Excluir conta de todos os meses"):
            st.session_state.contas_fixas = [c for c in st.session_state.contas_fixas if c['id'] != conta['id']]
            st.rerun()
            
    st.markdown(f"**Total Mês: R$ {total_fixas:.2f}**")

# ---> Colunas 2+: Cartões <---
for idx, cartao in enumerate(st.session_state.cartoes):
    with cols_despesas[idx + 1]:
        
        novo_nome = st.text_input(f"Editar Nome:", value=cartao["nome"], key=f"edit_nome_{cartao['id']}")
        if novo_nome != cartao["nome"]:
            st.session_state.cartoes[idx]["nome"] = novo_nome

        tem_dividas = any(c['cartao_id'] == cartao['id'] for c in st.session_state.compras_cartao)
        if not tem_dividas:
            if st.button("🗑️ Excluir Cartão", key=f"del_cartao_{cartao['id']}"):
                st.session_state.cartoes.pop(idx)
                st.rerun()

        st.markdown("---")
        
        with st.form(f"form_cartao_{cartao['id']}", clear_on_submit=True):
            desc_cartao = st.text_input("Descrição da Compra")
            c_val, c_parc = st.columns(2)
            val_cartao = c_val.number_input("Valor Total (R$)", min_value=0.0, step=10.0)
            parc_cartao = c_parc.number_input("Parcelas", min_value=1, step=1, value=1)
            
            btn_add_cartao_desp = st.form_submit_button("Adicionar")
            if btn_add_cartao_desp and desc_cartao and val_cartao > 0:
                st.session_state.compras_cartao.append({
                    "id": str(uuid.uuid4()),
                    "cartao_id": cartao["id"],
                    "desc": desc_cartao,
                    "valor_total": val_cartao,
                    "parcelas": parc_cartao,
                    "mes_inicio": mes_view
                })
                st.rerun()

        despesas_deste_cartao_neste_mes = [d for d in despesas_cartao_mes if d['cartao_id'] == cartao['id']]
        
        for desp in despesas_deste_cartao_neste_mes:
            c1, c2 = st.columns([4, 1])
            texto_parcela = f" ({desp['parcela_atual']}/{desp['total_parcelas']})" if desp['total_parcelas'] > 1 else ""
            c1.write(f"{desp['desc']}{texto_parcela}: R$ {desp['valor_parcela']:.2f}")
            
            if c2.button("❌", key=f"del_desp_{desp['id']}"):
                st.session_state.compras_cartao = [c for c in st.session_state.compras_cartao if c['id'] != desp['id']]
                st.rerun()

        total_cartao = sum(d['valor_parcela'] for d in despesas_deste_cartao_neste_mes)
        st.markdown(f"**Total Mês: R$ {total_cartao:.2f}**")

st.divider()

# --- Seção 3: Exportar para WhatsApp (Somente Cartões) ---
st.header("📱 Exportar Resumo do Mês (Cartões)")
st.caption("Clique no ícone de 'Copiar' no canto superior direito da caixa abaixo para enviar no WhatsApp.")

texto_export = ""

for cartao in st.session_state.cartoes:
    texto_export += f"{cartao['nome']}:\n\n"
    
    despesas_deste = [d for d in despesas_cartao_mes if d['cartao_id'] == cartao['id']]
    total_deste = sum(d['valor_parcela'] for d in despesas_deste)
    
    if not despesas_deste:
        texto_export += "Nenhuma despesa neste mês.\n"
    else:
        for d in despesas_deste:
            texto_export += f"o   {d['desc']}: R${d['valor_parcela']:.2f}\n".replace('.', ',')
            
    texto_export += f"\nTotal {cartao['nome']}: R${total_deste:.2f}\n\n".replace('.', ',')

st.code(texto_export.strip(), language="text")
