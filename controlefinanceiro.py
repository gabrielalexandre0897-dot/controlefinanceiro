import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

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

hoje = datetime.now()
mes_atual_str = f"{hoje.year:04d}-{hoje.month:02d}"

# --- Inicialização do Session State ---
if 'mes_view' not in st.session_state:
    st.session_state.mes_view = mes_atual_str
if 'salarios' not in st.session_state:
    st.session_state.salarios = {}
if 'rendas_extras' not in st.session_state:
    st.session_state.rendas_extras = [] 
if 'contas_fixas' not in st.session_state:
    st.session_state.contas_fixas = []
if 'pagamentos_fixas' not in st.session_state:
    st.session_state.pagamentos_fixas = {} # Formato: {"YYYY-MM_id": True/False}
if 'cartoes' not in st.session_state:
    st.session_state.cartoes = [
        {"id": "c1", "nome": "Cartão Dia 5"},
        {"id": "c2", "nome": "Cartão Dia 20"}
    ]
if 'compras_cartao' not in st.session_state:
    st.session_state.compras_cartao = []

mes_view = st.session_state.mes_view

# --- Lógica de Filtro e Cálculos do Mês Selecionado ---
# 1. Rendas
salario_mes = st.session_state.salarios.get(mes_view, 0.0)
rendas_mes = [r for r in st.session_state.rendas_extras if r['mes'] == mes_view]
total_receitas = salario_mes + sum(r['valor'] for r in rendas_mes)

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
saldo_projetado = total_receitas - total_despesas_geral # Quanto vai sobrar no fim de tudo

# --- Navegação de Meses ---
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
st.title("💸 Meu Controle Financeiro")

col_res1, col_res2, col_res3, col_res4 = st.columns(4)
col_res1.metric("💰 Receitas Totais", f"R$ {total_receitas:.2f}")
# Exibe despesas pendentes (vai diminuindo ao pagar)
col_res2.metric("📉 Despesas Pendentes", f"R$ {despesas_pendentes_geral:.2f}", delta=f"- R$ {total_fixas_pagas:.2f} pagas", delta_color="inverse")
col_res3.metric("✅ Contas Pagas (Mês)", f"R$ {total_fixas_pagas:.2f}")
# Saldo projetado (Receitas - Todas as despesas)
col_res4.metric("💲 Saldo Projetado Livre", f"R$ {saldo_projetado:.2f}")

st.write("") 

# --- Seção 1: Entradas (Ocultável) ---
with st.expander("💵 Minhas Rendas (Clique para expandir/ocultar)", expanded=False):
    col_renda1, col_renda2 = st.columns(2)
    with col_renda1:
        st.subheader("Salário Fixo do Mês")
        novo_salario = st.number_input("Valor do Salário (R$)", min_value=0.0, value=float(salario_mes), step=100.0)
        if novo_salario != salario_mes:
            st.session_state.salarios[mes_view] = novo_salario
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
                st.session_state.rendas_extras = [r for r in st.session_state.rendas_extras if r['id'] != renda['id']]
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
        
        # Checkbox para marcar como pago
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

# --- Seção 3: Exportar para WhatsApp (Baseado na Imagem) ---
st.header("📱 Exportar Resumo do Mês")
st.caption("Clique no ícone de 'Copiar' no canto superior direito da caixa abaixo para enviar no WhatsApp.")

# Montando o texto igual à imagem
texto_export = "Contas Fixas:\n"
for c in st.session_state.contas_fixas:
    texto_export += f"{c['desc']}: R${c['valor']:.2f}\n".replace('.', ',')

texto_export += "\n"

for cartao in st.session_state.cartoes:
    texto_export += f"{cartao['nome']}:\n\n"
    
    despesas_deste = [d for d in despesas_cartao_mes if d['cartao_id'] == cartao['id']]
    for d in despesas_deste:
        texto_export += f"o   {d['desc']}: R${d['valor_parcela']:.2f}\n".replace('.', ',')
    texto_export += "\n"

# st.code renderiza um bloco de texto com um botão de cópia nativo e muito bonito
st.code(texto_export.strip(), language="text")
