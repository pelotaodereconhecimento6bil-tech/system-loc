import os
from datetime import datetime

import pandas as pd
import streamlit as st
from database import conectar


PASTA_COMPROVANTES_DESPESAS = "comprovantes_despesas"


def salvar_comprovante_despesa(arquivo, veiculo_texto):
    if arquivo is None:
        return ""

    os.makedirs(PASTA_COMPROVANTES_DESPESAS, exist_ok=True)

    nome_base = veiculo_texto.replace(" ", "_").replace("-", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extensao = os.path.splitext(arquivo.name)[1].lower()

    if not extensao:
        extensao = ".bin"

    nome_arquivo = f"despesa_{nome_base}_{timestamp}{extensao}"
    caminho_arquivo = os.path.join(PASTA_COMPROVANTES_DESPESAS, nome_arquivo)

    with open(caminho_arquivo, "wb") as f:
        f.write(arquivo.getbuffer())

    return caminho_arquivo


def tela_despesas():
    st.subheader("Despesas do Veículo")

    conn = conectar()
    veiculos = pd.read_sql_query(
        "SELECT id, modelo, placa FROM veiculos ORDER BY modelo",
        conn
    )

    if veiculos.empty:
        st.info("Cadastre veículos antes de registrar despesas.")
        conn.close()
        return

    tab1, tab2, tab3, tab4 = st.tabs(["Nova despesa", "Histórico", "Editar", "Excluir"])

    with tab1:
        with st.form("form_despesa"):
            opcoes = {
                f"{row['modelo']} - {row['placa']}": row["id"]
                for _, row in veiculos.iterrows()
            }

            veiculo_escolhido = st.selectbox("Veículo", list(opcoes.keys()))
            data_despesa = st.date_input("Data da despesa")
            categoria = st.selectbox(
                "Categoria",
                [
                    "Seguro",
                    "IPVA",
                    "Licenciamento",
                    "Rastreador",
                    "Lavagem",
                    "Multa",
                    "Documentação",
                    "Guincho",
                    "Combustível",
                    "Manutenção",
                    "Outros",
                ]
            )
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, step=50.0)
            observacoes = st.text_area("Observações")
            comprovante = st.file_uploader(
                "Comprovante",
                type=["jpg", "jpeg", "png", "pdf", "doc", "docx", "webp"]
            )

            salvar = st.form_submit_button("Salvar despesa")

            if salvar:
                veiculo_id = opcoes[veiculo_escolhido]
                comprovante_path = salvar_comprovante_despesa(comprovante, veiculo_escolhido)

                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO despesas_veiculo (
                        veiculo_id, data_despesa, categoria, descricao,
                        valor, observacoes, comprovante_path
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    veiculo_id,
                    str(data_despesa),
                    categoria,
                    descricao,
                    valor,
                    observacoes,
                    comprovante_path
                ))
                conn.commit()
                st.success("Despesa registrada com sucesso.")
                st.rerun()

    df = pd.read_sql_query("""
        SELECT
            despesas_veiculo.id,
            despesas_veiculo.veiculo_id,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            despesas_veiculo.data_despesa,
            despesas_veiculo.categoria,
            despesas_veiculo.descricao,
            despesas_veiculo.valor,
            despesas_veiculo.observacoes,
            despesas_veiculo.comprovante_path
        FROM despesas_veiculo
        INNER JOIN veiculos ON despesas_veiculo.veiculo_id = veiculos.id
        ORDER BY despesas_veiculo.id DESC
    """, conn)

    with tab2:
        if df.empty:
            st.info("Nenhuma despesa cadastrada ainda.")
        else:
            st.dataframe(df.drop(columns=["veiculo_id", "comprovante_path"]), use_container_width=True)

            st.divider()
            st.markdown("### Baixar comprovante da despesa")

            opcoes_hist = {
                f"Despesa #{row['id']} - {row['veiculo']} - {row['categoria']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a despesa", list(opcoes_hist.keys()))
            registro = df[df["id"] == opcoes_hist[escolha]].iloc[0]

            caminho = registro["comprovante_path"]
            if caminho and os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    st.download_button(
                        "Baixar comprovante",
                        data=f,
                        file_name=os.path.basename(caminho),
                        use_container_width=True
                    )
            else:
                st.info("Esta despesa não possui comprovante.")

    with tab3:
        if df.empty:
            st.info("Nenhuma despesa cadastrada.")
        else:
            opcoes_edit = {
                f"Despesa #{row['id']} - {row['veiculo']} - {row['categoria']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a despesa para editar", list(opcoes_edit.keys()), key="editar_despesa")
            despesa_id = opcoes_edit[escolha]
            registro = df[df["id"] == despesa_id].iloc[0]

            categorias = [
                "Seguro", "IPVA", "Licenciamento", "Rastreador", "Lavagem",
                "Multa", "Documentação", "Guincho", "Combustível", "Manutenção", "Outros"
            ]

            with st.form("form_editar_despesa"):
                nova_data = st.text_input("Data", value=str(registro["data_despesa"]))
                nova_categoria = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(registro["categoria"]) if registro["categoria"] in categorias else 0
                )
                nova_descricao = st.text_input("Descrição", value=registro["descricao"] or "")
                novo_valor = st.number_input("Valor", min_value=0.0, value=float(registro["valor"] or 0), step=50.0)
                novas_observacoes = st.text_area("Observações", value=registro["observacoes"] or "")

                salvar_edicao = st.form_submit_button("Salvar alterações")

                if salvar_edicao:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE despesas_veiculo
                        SET data_despesa = ?, categoria = ?, descricao = ?, valor = ?, observacoes = ?
                        WHERE id = ?
                    """, (
                        nova_data,
                        nova_categoria,
                        nova_descricao,
                        novo_valor,
                        novas_observacoes,
                        despesa_id
                    ))
                    conn.commit()
                    st.success("Despesa atualizada com sucesso.")
                    st.rerun()

    with tab4:
        if df.empty:
            st.info("Nenhuma despesa cadastrada.")
        else:
            opcoes_exc = {
                f"Despesa #{row['id']} - {row['veiculo']} - {row['categoria']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a despesa para excluir", list(opcoes_exc.keys()), key="excluir_despesa")
            despesa_id = opcoes_exc[escolha]

            if st.button("Excluir despesa", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM despesas_veiculo WHERE id = ?", (despesa_id,))
                conn.commit()
                st.success("Despesa excluída com sucesso.")
                st.rerun()

    conn.close()