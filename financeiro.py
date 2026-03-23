import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from database import conectar


CORES_STATUS = {
    "Pendente": "#EF4444",
    "Parcial": "#F59E0B",
    "Pago": "#22C55E"
}


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tela_financeiro():
    st.subheader("Financeiro por Veículo")

    conn = conectar()

    receita_df = pd.read_sql_query("""
        SELECT
            veiculos.id,
            veiculos.modelo,
            veiculos.placa,
            COALESCE(SUM(contratos.valor_total_contrato), 0) AS total_contratado,
            COALESCE(SUM(contratos.valor_pago), 0) AS total_recebido,
            COUNT(contratos.id) AS total_contratos
        FROM veiculos
        LEFT JOIN contratos ON veiculos.id = contratos.veiculo_id
        GROUP BY veiculos.id, veiculos.modelo, veiculos.placa
        ORDER BY veiculos.modelo
    """, conn)

    manutencao_df = pd.read_sql_query("""
        SELECT
            veiculos.id,
            COALESCE(SUM(manutencoes.valor), 0) AS gasto_manutencao
        FROM veiculos
        LEFT JOIN manutencoes ON veiculos.id = manutencoes.veiculo_id
        GROUP BY veiculos.id
    """, conn)

    despesas_df = pd.read_sql_query("""
        SELECT
            veiculos.id,
            COALESCE(SUM(despesas_veiculo.valor), 0) AS outras_despesas
        FROM veiculos
        LEFT JOIN despesas_veiculo ON veiculos.id = despesas_veiculo.veiculo_id
        GROUP BY veiculos.id
    """, conn)

    contratos_pagamento_df = pd.read_sql_query("""
        SELECT
            status_pagamento,
            COUNT(*) AS quantidade
        FROM contratos
        GROUP BY status_pagamento
    """, conn)

    comprovantes_df = pd.read_sql_query("""
        SELECT
            contratos.id,
            clientes.nome AS cliente,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            contratos.valor_total_contrato,
            contratos.valor_pago,
            contratos.status_pagamento,
            contratos.data_pagamento,
            contratos.comprovante_pagamento,
            contratos.status
        FROM contratos
        INNER JOIN clientes ON contratos.cliente_id = clientes.id
        INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
        ORDER BY contratos.id DESC
    """, conn)

    conn.close()

    if receita_df.empty:
        st.info("Nenhum veículo cadastrado ainda.")
        return

    df = receita_df.merge(manutencao_df, on="id", how="left")
    df = df.merge(despesas_df, on="id", how="left")

    df["gasto_manutencao"] = df["gasto_manutencao"].fillna(0)
    df["outras_despesas"] = df["outras_despesas"].fillna(0)

    df["gasto_total"] = df["gasto_manutencao"] + df["outras_despesas"]
    df["total_pendente"] = df["total_contratado"] - df["total_recebido"]
    df["lucro_recebido"] = df["total_recebido"] - df["gasto_total"]
    df["lucro_projetado"] = df["total_contratado"] - df["gasto_total"]
    df["veiculo"] = df["modelo"] + " - " + df["placa"]

    total_contratado = df["total_contratado"].sum()
    total_recebido = df["total_recebido"].sum()
    total_pendente = df["total_pendente"].sum()
    total_gasto_manutencao = df["gasto_manutencao"].sum()
    total_outras_despesas = df["outras_despesas"].sum()
    total_gastos = df["gasto_total"].sum()
    total_lucro_recebido = df["lucro_recebido"].sum()
    total_lucro_projetado = df["lucro_projetado"].sum()

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

    c1, c2, c3 = st.columns(3)
    c1.metric("Total contratado", formatar_moeda(total_contratado))
    c2.metric("Total recebido", formatar_moeda(total_recebido))
    c3.metric("Total pendente", formatar_moeda(total_pendente))

    c4, c5, c6 = st.columns(3)
    c4.metric("Gasto manutenção", formatar_moeda(total_gasto_manutencao))
    c5.metric("Outras despesas", formatar_moeda(total_outras_despesas))
    c6.metric("Gasto total", formatar_moeda(total_gastos))

    c7, c8 = st.columns(2)
    c7.metric("Lucro sobre recebido", formatar_moeda(total_lucro_recebido))
    c8.metric("Lucro projetado", formatar_moeda(total_lucro_projetado))

    st.divider()
    st.markdown("### Visão gráfica")

    col1, col2 = st.columns(2)

    with col1:
        grafico_lucro = df.sort_values(by="lucro_recebido", ascending=False)

        fig1, ax1 = plt.subplots(figsize=(5.5, 2.8))
        ax1.plot(
            grafico_lucro["veiculo"],
            grafico_lucro["lucro_recebido"],
            marker="o",
            linewidth=1.8,
            markersize=4
        )

        ax1.set_title("Lucro por veículo", fontsize=10, pad=8, color=text_color)
        ax1.set_ylabel("R$", fontsize=8)
        ax1.set_xlabel("")
        ax1.grid(axis="y", alpha=0.20, color=grid_color)

        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.spines["left"].set_color(grid_color)
        ax1.spines["bottom"].set_color(grid_color)

        ax1.tick_params(axis="x", labelsize=8)
        ax1.tick_params(axis="y", labelsize=8)

        plt.xticks(rotation=35, ha="right")
        plt.tight_layout(pad=0.8)

        st.pyplot(fig1, clear_figure=True)

    with col2:
        valores_financeiro = [total_recebido, total_gastos, total_pendente]
        labels_financeiro = ["Recebido", "Gastos", "Pendente"]
        cores_financeiro = ["#22C55E", "#F59E0B", "#EF4444"]
        total_financeiro = sum(valores_financeiro)

        if total_financeiro > 0:
            fig2, ax2 = plt.subplots(figsize=(3.2, 3.2))

            wedges, texts, autotexts = ax2.pie(
                valores_financeiro,
                labels=labels_financeiro,
                colors=cores_financeiro,
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
                formatar_moeda(total_financeiro),
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="bold"
            )

            ax2.set_title("Financeiro", fontsize=10, pad=8, color=text_color)
            ax2.axis("equal")

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)

            st.pyplot(fig2, clear_figure=True)
        else:
            st.info("Sem dados financeiros suficientes para gerar o gráfico.")

    st.divider()
    st.markdown("### Resumo de pagamentos")

    if contratos_pagamento_df.empty:
        st.info("Nenhum contrato encontrado.")
   