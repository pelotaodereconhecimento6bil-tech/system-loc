<<<<<<< HEAD
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from auth import tela_login, logout
from database import criar_tabelas, conectar
from clientes import tela_clientes
from veiculos import tela_veiculos
from contratos import tela_contratos
from vistorias import tela_vistorias
from manutencoes import tela_manutencoes
from despesas import tela_despesas
from financeiro import tela_financeiro


st.set_page_config(
    page_title="Locadora System",
    page_icon="🚗",
    layout="wide"
)

criar_tabelas()

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""


def classificar_alerta(km_atual, km_limite):
    if km_limite is None or km_limite == 0:
        return None

    diferenca = km_limite - km_atual

    if diferenca < 0:
        return "Vencido"
    if diferenca <= 500:
        return "Urgente"
    if diferenca <= 1500:
        return "Próximo"
    return None


def montar_alertas_manutencao(df_manut):
    alertas = []

    if df_manut.empty:
        return pd.DataFrame()

    itens = [
        ("Troca de óleo", "proxima_troca_oleo"),
        ("Revisão", "km_prox_revisao"),
        ("Pneus", "km_prox_pneu"),
        ("Freios", "km_prox_freio"),
        ("Bateria", "km_prox_bateria"),
    ]

    for _, row in df_manut.iterrows():
        veiculo = f"{row['modelo']} - {row['placa']}"
        km_atual = row["km_atual"]

        for nome_item, coluna in itens:
            km_limite = row[coluna]
            status = classificar_alerta(km_atual, km_limite)

            if status:
                alertas.append({
                    "Veículo": veiculo,
                    "Item": nome_item,
                    "KM atual": km_atual,
                    "Próximo KM": km_limite,
                    "Status": status
                })

    return pd.DataFrame(alertas)


def carregar_indicadores():
    conn = conectar()

    total_clientes = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM clientes", conn
    ).iloc[0]["total"]

    total_veiculos = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos", conn
    ).iloc[0]["total"]

    veiculos_disponiveis = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos WHERE status = 'Disponível'", conn
    ).iloc[0]["total"]

    veiculos_alugados = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos WHERE status = 'Alugado'", conn
    ).iloc[0]["total"]

    contratos_ativos = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM contratos WHERE status = 'Ativo'", conn
    ).iloc[0]["total"]

    receita_recebida = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor_pago), 0) AS total
        FROM contratos
        WHERE status = 'Ativo'
        """,
        conn
    ).iloc[0]["total"]

    total_contratado = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor_total_contrato), 0) AS total
        FROM contratos
        WHERE status = 'Ativo'
        """,
        conn
    ).iloc[0]["total"]

    gasto_manutencao = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM manutencoes
        """,
        conn
    ).iloc[0]["total"]

    outras_despesas = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM despesas_veiculo
        """,
        conn
    ).iloc[0]["total"]

    contratos_recentes = pd.read_sql_query(
        """
        SELECT
            contratos.id,
            clientes.nome AS cliente,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            contratos.data_inicio,
            contratos.data_fim,
            contratos.valor_total_contrato,
            contratos.valor_pago,
            contratos.status_pagamento,
            contratos.status
        FROM contratos
        INNER JOIN clientes ON contratos.cliente_id = clientes.id
        INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
        ORDER BY contratos.id DESC
        LIMIT 5
        """,
        conn
    )

    ultimas_manutencoes = pd.read_sql_query(
        """
        SELECT
            m.veiculo_id,
            m.km_atual,
            m.proxima_troca_oleo,
            m.km_prox_revisao,
            m.km_prox_pneu,
            m.km_prox_freio,
            m.km_prox_bateria,
            v.modelo,
            v.placa
        FROM manutencoes m
        INNER JOIN (
            SELECT veiculo_id, MAX(id) AS ultimo_id
            FROM manutencoes
            GROUP BY veiculo_id
        ) ult ON m.id = ult.ultimo_id
        INNER JOIN veiculos v ON m.veiculo_id = v.id
        ORDER BY v.modelo
        """,
        conn
    )

    pagamentos_resumo = pd.read_sql_query(
        """
        SELECT
            status_pagamento,
            COUNT(*) AS quantidade
        FROM contratos
        GROUP BY status_pagamento
        """,
        conn
    )

    contratos_sem_comprovante = pd.read_sql_query(
        """
        SELECT
            contratos.id,
            clientes.nome AS cliente,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            contratos.valor_total_contrato,
            contratos.valor_pago,
            contratos.status_pagamento,
            contratos.data_pagamento,
            contratos.status
        FROM contratos
        INNER JOIN clientes ON contratos.cliente_id = clientes.id
        INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
        WHERE contratos.comprovante_pagamento IS NULL
           OR contratos.comprovante_pagamento = ''
        ORDER BY contratos.id DESC
        """,
        conn
    )

    conn.close()

    return {
        "total_clientes": total_clientes,
        "total_veiculos": total_veiculos,
        "veiculos_disponiveis": veiculos_disponiveis,
        "veiculos_alugados": veiculos_alugados,
        "contratos_ativos": contratos_ativos,
        "receita_recebida": receita_recebida,
        "total_contratado": total_contratado,
        "gasto_manutencao": gasto_manutencao,
        "outras_despesas": outras_despesas,
        "contratos_recentes": contratos_recentes,
        "ultimas_manutencoes": ultimas_manutencoes,
        "pagamentos_resumo": pagamentos_resumo,
        "contratos_sem_comprovante": contratos_sem_comprovante,
    }


def tela_inicio():
    st.subheader("Painel Geral")

    indicadores = carregar_indicadores()
    gasto_total = indicadores["gasto_manutencao"] + indicadores["outras_despesas"]

    bg_color = "#0E1117"
    text_color = "#EAEAEA"
    grid_color = "#2A2F3A"

    plt.rcParams.update({
        "figure.facecolor": bg_color,
        "axes.facecolor": bg_color,
        "savefig.facecolor": bg_color,
        "text.color": text_color,
        "axes.labelcolor": text_color,
        "xtick.color": text_color,
        "ytick.color": text_color,
        "axes.edgecolor": grid_color,
        "font.size": 10,
    })

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", indicadores["total_clientes"])
    col2.metric("Veículos", indicadores["total_veiculos"])
    col3.metric("Disponíveis", indicadores["veiculos_disponiveis"])
    col4.metric("Alugados", indicadores["veiculos_alugados"])

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Contratos ativos", indicadores["contratos_ativos"])
    col6.metric("Recebido (ativos)", f"R$ {indicadores['receita_recebida']:.2f}")
    col7.metric("Contratado (ativos)", f"R$ {indicadores['total_contratado']:.2f}")
    col8.metric("Gasto total", f"R$ {gasto_total:.2f}")

    st.divider()

    st.subheader("Últimos contratos")
    if indicadores["contratos_recentes"].empty:
        st.info("Nenhum contrato cadastrado ainda.")
    else:
        st.dataframe(indicadores["contratos_recentes"], use_container_width=True)

    st.divider()

    st.subheader("Alertas de manutenção preventiva")
    df_alertas = montar_alertas_manutencao(indicadores["ultimas_manutencoes"])

    if df_alertas.empty:
        st.success("Nenhum alerta de manutenção no momento.")
    else:
        df_vencidos = df_alertas[df_alertas["Status"] == "Vencido"]
        df_urgentes = df_alertas[df_alertas["Status"] == "Urgente"]
        df_proximos = df_alertas[df_alertas["Status"] == "Próximo"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Vencidos", len(df_vencidos))
        c2.metric("Urgentes", len(df_urgentes))
        c3.metric("Próximos", len(df_proximos))

        if not df_vencidos.empty:
            st.error("Existem manutenções vencidas.")
            st.dataframe(df_vencidos, use_container_width=True)

        if not df_urgentes.empty:
            st.warning("Existem manutenções em estado urgente.")
            st.dataframe(df_urgentes, use_container_width=True)

        if not df_proximos.empty:
            st.info("Existem manutenções próximas.")
            st.dataframe(df_proximos, use_container_width=True)

    st.divider()

    st.subheader("Alertas de pagamentos e comprovantes")

    pagamentos = indicadores["pagamentos_resumo"]
    contratos_sem = indicadores["contratos_sem_comprovante"]

    resumo_pagamentos = {}
    if not pagamentos.empty:
        resumo_pagamentos = {
            row["status_pagamento"]: row["quantidade"]
            for _, row in pagamentos.iterrows()
        }

    pendentes = resumo_pagamentos.get("Pendente", 0)
    parciais = resumo_pagamentos.get("Parcial", 0)
    pagos = resumo_pagamentos.get("Pago", 0)

    sem_comprovante_pago = (
        len(contratos_sem[contratos_sem["status_pagamento"] == "Pago"])
        if not contratos_sem.empty else 0
    )

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Pendentes", pendentes)
    a2.metric("Parciais", parciais)
    a3.metric("Pagos", pagos)
    a4.metric("Pagos sem comprovante", sem_comprovante_pago)

    if contratos_sem.empty:
        st.success("Nenhum contrato sem comprovante no momento.")
    else:
        st.dataframe(contratos_sem, use_container_width=True)

    st.divider()
    st.subheader("Resumo visual")

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        labels_status = ["Disponíveis", "Alugados"]
        valores_status = [
            indicadores["veiculos_disponiveis"],
            indicadores["veiculos_alugados"],
        ]
        total_status = sum(valores_status)

        if total_status > 0:
            fig1, ax1 = plt.subplots(figsize=(3.3, 3.3))

            wedges, texts, autotexts = ax1.pie(
                valores_status,
                labels=labels_status,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.34,
                    "edgecolor": bg_color,
                    "linewidth": 2
                },
                textprops={
                    "color": text_color,
                    "fontsize": 8
                }
            )

            ax1.text(
                0, 0,
                f"{total_status}\nveículos",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold"
            )

            ax1.set_title("Frota", fontsize=10, pad=8, color=text_color)
            ax1.axis("equal")

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)

            st.pyplot(fig1, clear_figure=True)
        else:
            st.info("Sem dados da frota para gerar gráfico.")

    with col_graf2:
        labels_pg = ["Pendente", "Parcial", "Pago"]
        valores_pg = [pendentes, parciais, pagos]
        total_pg = sum(valores_pg)

        if total_pg > 0:
            fig2, ax2 = plt.subplots(figsize=(3.3, 3.3))

            wedges, texts, autotexts = ax2.pie(
                valores_pg,
                labels=labels_pg,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.34,
                    "edgecolor": bg_color,
                    "linewidth": 2
                },
                textprops={
                    "color": text_color,
                    "fontsize": 8
                }
            )

            ax2.text(
                0, 0,
                f"{total_pg}\npagamentos",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold"
            )

            ax2.set_title("Pagamentos", fontsize=10, pad=8, color=text_color)
            ax2.axis("equal")

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)

            st.pyplot(fig2, clear_figure=True)
        else:
            st.info("Sem dados de pagamentos para gerar gráfico.")

    st.divider()
    st.subheader("Atalhos")

    at1, at2, at3, at4 = st.columns(4)

    with at1:
        st.info("Cadastre clientes e veículos antes de gerar contratos.")

    with at2:
        st.info("Use Vistorias para registrar KM, fotos e observações.")

    with at3:
        st.info("Use Manutenções e Despesas para acompanhar custos.")

    with at4:
        st.info("Use Contratos e Financeiro para controlar recebimentos.")


if not st.session_state["logado"]:
    tela_login()
else:
    st.sidebar.success(f"Usuário: {st.session_state['usuario']}")

    if st.sidebar.button("Sair"):
        logout()

    st.title("🚗 Locadora System")
    st.caption("Sistema interno de gestão da locadora")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "Início",
            "Clientes",
            "Veículos",
            "Contratos",
            "Vistorias",
            "Manutenções",
            "Despesas",
            "Financeiro"
        ]
    )

    if menu == "Início":
        tela_inicio()
    elif menu == "Clientes":
        tela_clientes()
    elif menu == "Veículos":
        tela_veiculos()
    elif menu == "Contratos":
        tela_contratos()
    elif menu == "Vistorias":
        tela_vistorias()
    elif menu == "Manutenções":
        tela_manutencoes()
    elif menu == "Despesas":
        tela_despesas()
    elif menu == "Financeiro":
=======
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from auth import tela_login, logout
from database import criar_tabelas, conectar
from clientes import tela_clientes
from veiculos import tela_veiculos
from contratos import tela_contratos
from vistorias import tela_vistorias
from manutencoes import tela_manutencoes
from despesas import tela_despesas
from financeiro import tela_financeiro


st.set_page_config(
    page_title="Locadora System",
    page_icon="🚗",
    layout="wide"
)

criar_tabelas()

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""


def classificar_alerta(km_atual, km_limite):
    if km_limite is None or km_limite == 0:
        return None

    diferenca = km_limite - km_atual

    if diferenca < 0:
        return "Vencido"
    if diferenca <= 500:
        return "Urgente"
    if diferenca <= 1500:
        return "Próximo"
    return None


def montar_alertas_manutencao(df_manut):
    alertas = []

    if df_manut.empty:
        return pd.DataFrame()

    itens = [
        ("Troca de óleo", "proxima_troca_oleo"),
        ("Revisão", "km_prox_revisao"),
        ("Pneus", "km_prox_pneu"),
        ("Freios", "km_prox_freio"),
        ("Bateria", "km_prox_bateria"),
    ]

    for _, row in df_manut.iterrows():
        veiculo = f"{row['modelo']} - {row['placa']}"
        km_atual = row["km_atual"]

        for nome_item, coluna in itens:
            km_limite = row[coluna]
            status = classificar_alerta(km_atual, km_limite)

            if status:
                alertas.append({
                    "Veículo": veiculo,
                    "Item": nome_item,
                    "KM atual": km_atual,
                    "Próximo KM": km_limite,
                    "Status": status
                })

    return pd.DataFrame(alertas)


def carregar_indicadores():
    conn = conectar()

    total_clientes = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM clientes", conn
    ).iloc[0]["total"]

    total_veiculos = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos", conn
    ).iloc[0]["total"]

    veiculos_disponiveis = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos WHERE status = 'Disponível'", conn
    ).iloc[0]["total"]

    veiculos_alugados = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM veiculos WHERE status = 'Alugado'", conn
    ).iloc[0]["total"]

    contratos_ativos = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM contratos WHERE status = 'Ativo'", conn
    ).iloc[0]["total"]

    receita_recebida = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor_pago), 0) AS total
        FROM contratos
        WHERE status = 'Ativo'
        """,
        conn
    ).iloc[0]["total"]

    total_contratado = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor_total_contrato), 0) AS total
        FROM contratos
        WHERE status = 'Ativo'
        """,
        conn
    ).iloc[0]["total"]

    gasto_manutencao = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM manutencoes
        """,
        conn
    ).iloc[0]["total"]

    outras_despesas = pd.read_sql_query(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM despesas_veiculo
        """,
        conn
    ).iloc[0]["total"]

    contratos_recentes = pd.read_sql_query(
        """
        SELECT
            contratos.id,
            clientes.nome AS cliente,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            contratos.data_inicio,
            contratos.data_fim,
            contratos.valor_total_contrato,
            contratos.valor_pago,
            contratos.status_pagamento,
            contratos.status
        FROM contratos
        INNER JOIN clientes ON contratos.cliente_id = clientes.id
        INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
        ORDER BY contratos.id DESC
        LIMIT 5
        """,
        conn
    )

    ultimas_manutencoes = pd.read_sql_query(
        """
        SELECT
            m.veiculo_id,
            m.km_atual,
            m.proxima_troca_oleo,
            m.km_prox_revisao,
            m.km_prox_pneu,
            m.km_prox_freio,
            m.km_prox_bateria,
            v.modelo,
            v.placa
        FROM manutencoes m
        INNER JOIN (
            SELECT veiculo_id, MAX(id) AS ultimo_id
            FROM manutencoes
            GROUP BY veiculo_id
        ) ult ON m.id = ult.ultimo_id
        INNER JOIN veiculos v ON m.veiculo_id = v.id
        ORDER BY v.modelo
        """,
        conn
    )

    pagamentos_resumo = pd.read_sql_query(
        """
        SELECT
            status_pagamento,
            COUNT(*) AS quantidade
        FROM contratos
        GROUP BY status_pagamento
        """,
        conn
    )

    contratos_sem_comprovante = pd.read_sql_query(
        """
        SELECT
            contratos.id,
            clientes.nome AS cliente,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            contratos.valor_total_contrato,
            contratos.valor_pago,
            contratos.status_pagamento,
            contratos.data_pagamento,
            contratos.status
        FROM contratos
        INNER JOIN clientes ON contratos.cliente_id = clientes.id
        INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
        WHERE contratos.comprovante_pagamento IS NULL
           OR contratos.comprovante_pagamento = ''
        ORDER BY contratos.id DESC
        """,
        conn
    )

    conn.close()

    return {
        "total_clientes": total_clientes,
        "total_veiculos": total_veiculos,
        "veiculos_disponiveis": veiculos_disponiveis,
        "veiculos_alugados": veiculos_alugados,
        "contratos_ativos": contratos_ativos,
        "receita_recebida": receita_recebida,
        "total_contratado": total_contratado,
        "gasto_manutencao": gasto_manutencao,
        "outras_despesas": outras_despesas,
        "contratos_recentes": contratos_recentes,
        "ultimas_manutencoes": ultimas_manutencoes,
        "pagamentos_resumo": pagamentos_resumo,
        "contratos_sem_comprovante": contratos_sem_comprovante,
    }


def tela_inicio():
    st.subheader("Painel Geral")

    indicadores = carregar_indicadores()
    gasto_total = indicadores["gasto_manutencao"] + indicadores["outras_despesas"]

    bg_color = "#0E1117"
    text_color = "#EAEAEA"
    grid_color = "#2A2F3A"

    plt.rcParams.update({
        "figure.facecolor": bg_color,
        "axes.facecolor": bg_color,
        "savefig.facecolor": bg_color,
        "text.color": text_color,
        "axes.labelcolor": text_color,
        "xtick.color": text_color,
        "ytick.color": text_color,
        "axes.edgecolor": grid_color,
        "font.size": 10,
    })

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", indicadores["total_clientes"])
    col2.metric("Veículos", indicadores["total_veiculos"])
    col3.metric("Disponíveis", indicadores["veiculos_disponiveis"])
    col4.metric("Alugados", indicadores["veiculos_alugados"])

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Contratos ativos", indicadores["contratos_ativos"])
    col6.metric("Recebido (ativos)", f"R$ {indicadores['receita_recebida']:.2f}")
    col7.metric("Contratado (ativos)", f"R$ {indicadores['total_contratado']:.2f}")
    col8.metric("Gasto total", f"R$ {gasto_total:.2f}")

    st.divider()

    st.subheader("Últimos contratos")
    if indicadores["contratos_recentes"].empty:
        st.info("Nenhum contrato cadastrado ainda.")
    else:
        st.dataframe(indicadores["contratos_recentes"], use_container_width=True)

    st.divider()

    st.subheader("Alertas de manutenção preventiva")
    df_alertas = montar_alertas_manutencao(indicadores["ultimas_manutencoes"])

    if df_alertas.empty:
        st.success("Nenhum alerta de manutenção no momento.")
    else:
        df_vencidos = df_alertas[df_alertas["Status"] == "Vencido"]
        df_urgentes = df_alertas[df_alertas["Status"] == "Urgente"]
        df_proximos = df_alertas[df_alertas["Status"] == "Próximo"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Vencidos", len(df_vencidos))
        c2.metric("Urgentes", len(df_urgentes))
        c3.metric("Próximos", len(df_proximos))

        if not df_vencidos.empty:
            st.error("Existem manutenções vencidas.")
            st.dataframe(df_vencidos, use_container_width=True)

        if not df_urgentes.empty:
            st.warning("Existem manutenções em estado urgente.")
            st.dataframe(df_urgentes, use_container_width=True)

        if not df_proximos.empty:
            st.info("Existem manutenções próximas.")
            st.dataframe(df_proximos, use_container_width=True)

    st.divider()

    st.subheader("Alertas de pagamentos e comprovantes")

    pagamentos = indicadores["pagamentos_resumo"]
    contratos_sem = indicadores["contratos_sem_comprovante"]

    resumo_pagamentos = {}
    if not pagamentos.empty:
        resumo_pagamentos = {
            row["status_pagamento"]: row["quantidade"]
            for _, row in pagamentos.iterrows()
        }

    pendentes = resumo_pagamentos.get("Pendente", 0)
    parciais = resumo_pagamentos.get("Parcial", 0)
    pagos = resumo_pagamentos.get("Pago", 0)

    sem_comprovante_pago = (
        len(contratos_sem[contratos_sem["status_pagamento"] == "Pago"])
        if not contratos_sem.empty else 0
    )

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Pendentes", pendentes)
    a2.metric("Parciais", parciais)
    a3.metric("Pagos", pagos)
    a4.metric("Pagos sem comprovante", sem_comprovante_pago)

    if contratos_sem.empty:
        st.success("Nenhum contrato sem comprovante no momento.")
    else:
        st.dataframe(contratos_sem, use_container_width=True)

    st.divider()
    st.subheader("Resumo visual")

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        labels_status = ["Disponíveis", "Alugados"]
        valores_status = [
            indicadores["veiculos_disponiveis"],
            indicadores["veiculos_alugados"],
        ]
        total_status = sum(valores_status)

        if total_status > 0:
            fig1, ax1 = plt.subplots(figsize=(3.3, 3.3))

            wedges, texts, autotexts = ax1.pie(
                valores_status,
                labels=labels_status,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.34,
                    "edgecolor": bg_color,
                    "linewidth": 2
                },
                textprops={
                    "color": text_color,
                    "fontsize": 8
                }
            )

            ax1.text(
                0, 0,
                f"{total_status}\nveículos",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold"
            )

            ax1.set_title("Frota", fontsize=10, pad=8, color=text_color)
            ax1.axis("equal")

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)

            st.pyplot(fig1, clear_figure=True)
        else:
            st.info("Sem dados da frota para gerar gráfico.")

    with col_graf2:
        labels_pg = ["Pendente", "Parcial", "Pago"]
        valores_pg = [pendentes, parciais, pagos]
        total_pg = sum(valores_pg)

        if total_pg > 0:
            fig2, ax2 = plt.subplots(figsize=(3.3, 3.3))

            wedges, texts, autotexts = ax2.pie(
                valores_pg,
                labels=labels_pg,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.34,
                    "edgecolor": bg_color,
                    "linewidth": 2
                },
                textprops={
                    "color": text_color,
                    "fontsize": 8
                }
            )

            ax2.text(
                0, 0,
                f"{total_pg}\npagamentos",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold"
            )

            ax2.set_title("Pagamentos", fontsize=10, pad=8, color=text_color)
            ax2.axis("equal")

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)

            st.pyplot(fig2, clear_figure=True)
        else:
            st.info("Sem dados de pagamentos para gerar gráfico.")

    st.divider()
    st.subheader("Atalhos")

    at1, at2, at3, at4 = st.columns(4)

    with at1:
        st.info("Cadastre clientes e veículos antes de gerar contratos.")

    with at2:
        st.info("Use Vistorias para registrar KM, fotos e observações.")

    with at3:
        st.info("Use Manutenções e Despesas para acompanhar custos.")

    with at4:
        st.info("Use Contratos e Financeiro para controlar recebimentos.")


if not st.session_state["logado"]:
    tela_login()
else:
    st.sidebar.success(f"Usuário: {st.session_state['usuario']}")

    if st.sidebar.button("Sair"):
        logout()

    st.title("🚗 Locadora System")
    st.caption("Sistema interno de gestão da locadora")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "Início",
            "Clientes",
            "Veículos",
            "Contratos",
            "Vistorias",
            "Manutenções",
            "Despesas",
            "Financeiro"
        ]
    )

    if menu == "Início":
        tela_inicio()
    elif menu == "Clientes":
        tela_clientes()
    elif menu == "Veículos":
        tela_veiculos()
    elif menu == "Contratos":
        tela_contratos()
    elif menu == "Vistorias":
        tela_vistorias()
    elif menu == "Manutenções":
        tela_manutencoes()
    elif menu == "Despesas":
        tela_despesas()
    elif menu == "Financeiro":
>>>>>>> 4f4d18623026bf11e99f258282f6ff8da67220f9
        tela_financeiro()