import pandas as pd
import streamlit as st
from database import conectar
from utils import (
    buscar_cep,
    formatar_nome,
    formatar_cpf,
    formatar_rg,
    formatar_telefone,
    formatar_cep,
)


def tela_clientes():
    st.subheader("Cadastro de Clientes")

    tab1, tab2, tab3 = st.tabs(["Cadastrar", "Editar", "Excluir"])

    with tab1:
        st.markdown("### Novo cliente")

        if "cliente_endereco_auto" not in st.session_state:
            st.session_state.cliente_endereco_auto = ""
            st.session_state.cliente_cidade_auto = ""
            st.session_state.cliente_estado_auto = ""

        with st.form("form_cliente"):
            nome = st.text_input("Nome completo")
            cpf = st.text_input("CPF")
            rg = st.text_input("RG")
            telefone = st.text_input("Telefone")

            col1, col2 = st.columns([2, 1])
            with col1:
                cep = st.text_input("CEP")
            with col2:
                buscar = st.form_submit_button("Buscar CEP")

            if buscar:
                dados_cep = buscar_cep(cep)
                if dados_cep:
                    st.session_state.cliente_endereco_auto = dados_cep["endereco"]
                    st.session_state.cliente_cidade_auto = dados_cep["cidade"]
                    st.session_state.cliente_estado_auto = dados_cep["estado"]
                    st.success("CEP encontrado.")
                else:
                    st.warning("CEP não encontrado.")

            endereco = st.text_input("Endereço", value=st.session_state.cliente_endereco_auto)
            cidade = st.text_input("Cidade", value=st.session_state.cliente_cidade_auto)
            estado = st.text_input("Estado", value=st.session_state.cliente_estado_auto)

            salvar = st.form_submit_button("Salvar cliente")

            if salvar:
                nome = formatar_nome(nome)
                cpf = formatar_cpf(cpf)
                rg = formatar_rg(rg)
                telefone = formatar_telefone(telefone)
                cep = formatar_cep(cep)
                cidade = formatar_nome(cidade)
                estado = estado.strip().upper()

                if not nome:
                    st.error("O nome do cliente é obrigatório.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (
                            nome, cpf, rg, telefone, endereco, cidade, estado, cep
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nome, cpf, rg, telefone, endereco, cidade, estado, cep))
                    conn.commit()
                    conn.close()
                    st.success("Cliente cadastrado com sucesso.")
                    st.rerun()

    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY id DESC", conn)

    with tab2:
        if df.empty:
            st.info("Nenhum cliente cadastrado ainda.")
        else:
            opcoes = {
                f"{row['nome']} - CPF: {row['cpf']}": row["id"]
                for _, row in df.iterrows()
            }

            cliente_escolhido = st.selectbox(
                "Selecione o cliente para editar",
                list(opcoes.keys()),
                key="editar_cliente"
            )
            cliente_id = opcoes[cliente_escolhido]
            cliente = df[df["id"] == cliente_id].iloc[0]

            with st.form("form_editar_cliente"):
                novo_nome = st.text_input("Nome completo", value=cliente["nome"] or "")
                novo_cpf = st.text_input("CPF", value=cliente["cpf"] or "")
                novo_rg = st.text_input("RG", value=cliente["rg"] or "")
                novo_telefone = st.text_input("Telefone", value=cliente["telefone"] or "")
                novo_endereco = st.text_input("Endereço", value=cliente["endereco"] or "")
                nova_cidade = st.text_input("Cidade", value=cliente["cidade"] or "")
                novo_estado = st.text_input("Estado", value=cliente["estado"] or "")
                novo_cep = st.text_input("CEP", value=cliente["cep"] or "")

                atualizar = st.form_submit_button("Atualizar cliente")

                if atualizar:
                    novo_nome = formatar_nome(novo_nome)
                    novo_cpf = formatar_cpf(novo_cpf)
                    novo_rg = formatar_rg(novo_rg)
                    novo_telefone = formatar_telefone(novo_telefone)
                    novo_cep = formatar_cep(novo_cep)
                    nova_cidade = formatar_nome(nova_cidade)
                    novo_estado = novo_estado.strip().upper()

                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE clientes
                        SET nome = ?, cpf = ?, rg = ?, telefone = ?, endereco = ?, cidade = ?, estado = ?, cep = ?
                        WHERE id = ?
                    """, (
                        novo_nome,
                        novo_cpf,
                        novo_rg,
                        novo_telefone,
                        novo_endereco,
                        nova_cidade,
                        novo_estado,
                        novo_cep,
                        cliente_id
                    ))
                    conn.commit()
                    st.success("Cliente atualizado com sucesso.")
                    st.rerun()

    with tab3:
        if df.empty:
            st.info("Nenhum cliente cadastrado ainda.")
        else:
            opcoes = {
                f"{row['nome']} - CPF: {row['cpf']}": row["id"]
                for _, row in df.iterrows()
            }

            cliente_excluir = st.selectbox(
                "Selecione o cliente para excluir",
                list(opcoes.keys()),
                key="excluir_cliente"
            )
            cliente_id_excluir = opcoes[cliente_excluir]

            st.warning("Atenção: se houver contratos vinculados, revise antes de excluir.")

            if st.button("Excluir cliente", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id_excluir,))
                conn.commit()
                st.success("Cliente excluído com sucesso.")
                st.rerun()

    st.divider()
    st.subheader("Clientes cadastrados")

    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        st.dataframe(df, use_container_width=True)