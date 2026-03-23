import pandas as pd
import streamlit as st
from database import conectar
from utils import formatar_placa


def tela_veiculos():
    st.subheader("Cadastro de Veículos")

    tab1, tab2, tab3 = st.tabs(["Cadastrar", "Editar", "Excluir"])

    with tab1:
        with st.form("form_veiculo"):
            modelo = st.text_input("Modelo")
            marca = st.text_input("Marca")
            ano = st.text_input("Ano")
            placa = st.text_input("Placa")
            cor = st.text_input("Cor")
            status = st.selectbox(
                "Status",
                ["Disponível", "Alugado", "Reservado", "Em manutenção"]
            )
            observacoes = st.text_area("Observações")

            salvar = st.form_submit_button("Salvar veículo")

            if salvar:
                placa = formatar_placa(placa)

                if not modelo:
                    st.error("O modelo do veículo é obrigatório.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO veiculos (modelo, marca, ano, placa, cor, status, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (modelo, marca, ano, placa, cor, status, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Veículo cadastrado com sucesso.")
                    st.rerun()

    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM veiculos ORDER BY id DESC", conn)

    with tab2:
        if df.empty:
            st.info("Nenhum veículo cadastrado ainda.")
        else:
            opcoes = {
                f"{row['modelo']} - {row['placa']}": row["id"]
                for _, row in df.iterrows()
            }

            veiculo_escolhido = st.selectbox(
                "Selecione o veículo para editar",
                list(opcoes.keys()),
                key="editar_veiculo"
            )
            veiculo_id = opcoes[veiculo_escolhido]
            veiculo = df[df["id"] == veiculo_id].iloc[0]

            status_lista = ["Disponível", "Alugado", "Reservado", "Em manutenção"]
            status_atual = veiculo["status"] if veiculo["status"] in status_lista else "Disponível"

            with st.form("form_editar_veiculo"):
                novo_modelo = st.text_input("Modelo", value=veiculo["modelo"] or "")
                nova_marca = st.text_input("Marca", value=veiculo["marca"] or "")
                novo_ano = st.text_input("Ano", value=veiculo["ano"] or "")
                nova_placa = st.text_input("Placa", value=veiculo["placa"] or "")
                nova_cor = st.text_input("Cor", value=veiculo["cor"] or "")
                novo_status = st.selectbox(
                    "Status",
                    status_lista,
                    index=status_lista.index(status_atual)
                )
                novas_observacoes = st.text_area("Observações", value=veiculo["observacoes"] or "")

                atualizar = st.form_submit_button("Atualizar veículo")

                if atualizar:
                    nova_placa = formatar_placa(nova_placa)

                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE veiculos
                        SET modelo = ?, marca = ?, ano = ?, placa = ?, cor = ?, status = ?, observacoes = ?
                        WHERE id = ?
                    """, (
                        novo_modelo,
                        nova_marca,
                        novo_ano,
                        nova_placa,
                        nova_cor,
                        novo_status,
                        novas_observacoes,
                        veiculo_id
                    ))
                    conn.commit()
                    st.success("Veículo atualizado com sucesso.")
                    st.rerun()

    with tab3:
        if df.empty:
            st.info("Nenhum veículo cadastrado ainda.")
        else:
            opcoes = {
                f"{row['modelo']} - {row['placa']}": row["id"]
                for _, row in df.iterrows()
            }

            veiculo_excluir = st.selectbox(
                "Selecione o veículo para excluir",
                list(opcoes.keys()),
                key="excluir_veiculo"
            )
            veiculo_id_excluir = opcoes[veiculo_excluir]

            st.warning("Atenção: excluir veículo pode afetar contratos, vistorias e manutenções.")

            if st.button("Excluir veículo", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id_excluir,))
                conn.commit()
                st.success("Veículo excluído com sucesso.")
                st.rerun()

    st.divider()
    st.subheader("Veículos cadastrados")

    df = pd.read_sql_query("SELECT * FROM veiculos ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.info("Nenhum veículo cadastrado ainda.")
    else:
        st.dataframe(df, use_container_width=True)