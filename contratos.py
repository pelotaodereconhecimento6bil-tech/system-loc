import math
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from docxtpl import DocxTemplate

from database import conectar
from utils import (
    buscar_cep,
    valor_por_extenso,
    data_por_extenso,
    duracao_texto,
    formatar_nome,
    formatar_cpf,
    formatar_rg,
    formatar_moeda,
    formatar_cep,
)

TEMPLATE_PATH = "templates/contrato_template.docx"
OUTPUT_DIR = "contratos_gerados"
COMPROVANTES_DIR = "comprovantes_pagamento"


def gerar_contrato_docx(dados):
    if not os.path.exists(TEMPLATE_PATH):
        return None, f"Template não encontrado em: {TEMPLATE_PATH}"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    nome_limpo = dados["locatario_nome"]
    nome_limpo = re.sub(r"[^\w\s]", "", nome_limpo).replace(" ", "_")

    placa_limpa = re.sub(r"[^\w\s]", "", dados["veiculo_placa"]).replace(" ", "_")
    nome_arquivo = f"contrato_{nome_limpo}_{placa_limpa}.docx"
    caminho_arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)

    doc = DocxTemplate(TEMPLATE_PATH)
    doc.render(dados)
    doc.save(caminho_arquivo)

    return caminho_arquivo, None


def salvar_comprovante(contrato_id, arquivo):
    if arquivo is None:
        return ""

    os.makedirs(COMPROVANTES_DIR, exist_ok=True)

    extensao = os.path.splitext(arquivo.name)[1].lower()
    if not extensao:
        extensao = ".bin"

    nome_arquivo = f"comprovante_contrato_{contrato_id}{extensao}"
    caminho = os.path.join(COMPROVANTES_DIR, nome_arquivo)

    with open(caminho, "wb") as f:
        f.write(arquivo.getbuffer())

    return caminho


def calcular_semanas_cobradas(data_inicio, data_fim):
    dias = (data_fim - data_inicio).days + 1
    return max(1, math.ceil(dias / 7))


def finalizar_contrato(contrato_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT veiculo_id, status
        FROM contratos
        WHERE id = ?
    """, (contrato_id,))
    contrato = cursor.fetchone()

    if not contrato:
        conn.close()
        return False, "Contrato não encontrado."

    veiculo_id, status_atual = contrato

    if status_atual == "Finalizado":
        conn.close()
        return False, "Este contrato já está finalizado."

    cursor.execute("""
        UPDATE contratos
        SET status = 'Finalizado'
        WHERE id = ?
    """, (contrato_id,))

    cursor.execute("""
        UPDATE veiculos
        SET status = 'Disponível'
        WHERE id = ?
    """, (veiculo_id,))

    conn.commit()
    conn.close()
    return True, "Contrato finalizado com sucesso. Veículo liberado."


def atualizar_pagamento(contrato_id, valor_pago, status_pagamento, data_pagamento, comprovante_path=None):
    conn = conectar()
    cursor = conn.cursor()

    if comprovante_path:
        cursor.execute("""
            UPDATE contratos
            SET valor_pago = ?, status_pagamento = ?, data_pagamento = ?, comprovante_pagamento = ?
            WHERE id = ?
        """, (valor_pago, status_pagamento, data_pagamento, comprovante_path, contrato_id))
    else:
        cursor.execute("""
            UPDATE contratos
            SET valor_pago = ?, status_pagamento = ?, data_pagamento = ?
            WHERE id = ?
        """, (valor_pago, status_pagamento, data_pagamento, contrato_id))

    conn.commit()
    conn.close()


def tela_contratos():
    st.subheader("Gestão de Contratos")

    conn = conectar()

    clientes = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    veiculos = pd.read_sql_query(
        """
        SELECT id, modelo, marca, ano, placa, cor, status
        FROM veiculos
        ORDER BY modelo
        """,
        conn,
    )

    if "contrato_endereco_auto" not in st.session_state:
        st.session_state.contrato_endereco_auto = ""
        st.session_state.contrato_cidade_auto = ""
        st.session_state.contrato_estado_auto = ""

    if "arquivo_contrato_gerado" not in st.session_state:
        st.session_state.arquivo_contrato_gerado = None

    if "nome_arquivo_contrato_gerado" not in st.session_state:
        st.session_state.nome_arquivo_contrato_gerado = None

    tab1, tab2 = st.tabs(["Novo contrato", "Lista de contratos"])

    with tab1:
        if clientes.empty:
            st.warning("Cadastre clientes primeiro.")
            conn.close()
            return

        if veiculos.empty:
            st.warning("Cadastre veículos primeiro.")
            conn.close()
            return

        veiculos_disponiveis = veiculos[veiculos["status"] == "Disponível"]

        if veiculos_disponiveis.empty:
            st.info("Sem veículos disponíveis.")
        else:
            cliente_opcoes = {f"{row['nome']}": row["id"] for _, row in clientes.iterrows()}
            cliente_nome_escolhido = st.selectbox("Cliente", list(cliente_opcoes.keys()))
            cliente_id = cliente_opcoes[cliente_nome_escolhido]
            cliente = clientes[clientes["id"] == cliente_id].iloc[0]

            st.markdown("### Endereço do contrato")

            col_cep1, col_cep2 = st.columns([2, 1])
            with col_cep1:
                cep_busca = st.text_input(
                    "CEP para buscar",
                    value=cliente["cep"] or "",
                    key="cep_busca_contrato"
                )
            with col_cep2:
                st.write("")
                st.write("")
                if st.button("Buscar CEP"):
                    dados_cep = buscar_cep(cep_busca)
                    if dados_cep:
                        st.session_state.contrato_endereco_auto = dados_cep["endereco"]
                        st.session_state.contrato_cidade_auto = dados_cep["cidade"]
                        st.session_state.contrato_estado_auto = dados_cep["estado"]
                        st.success("CEP encontrado.")
                    else:
                        st.warning("CEP não encontrado.")

            with st.form("form_contrato"):
                st.markdown("### Cliente selecionado")
                st.info(f"Cliente: {cliente['nome']}")

                cep = st.text_input("CEP final", value=cep_busca)
                endereco = st.text_input(
                    "Endereço",
                    value=st.session_state.contrato_endereco_auto or (cliente["endereco"] or "")
                )
                cidade = st.text_input(
                    "Cidade",
                    value=st.session_state.contrato_cidade_auto or (cliente["cidade"] or "")
                )
                estado = st.text_input(
                    "Estado",
                    value=st.session_state.contrato_estado_auto or (cliente["estado"] or "")
                )

                st.markdown("### Veículo")
                veiculo_opcoes = {
                    f"{row['modelo']} - {row['placa']}": row["id"]
                    for _, row in veiculos_disponiveis.iterrows()
                }

                veiculo_escolhido = st.selectbox("Veículo", list(veiculo_opcoes.keys()))
                veiculo_id = veiculo_opcoes[veiculo_escolhido]
                veiculo = veiculos[veiculos["id"] == veiculo_id].iloc[0]

                st.markdown("### Período")
                data_inicio = st.date_input("Data início")
                data_fim = st.date_input("Data fim")

                st.markdown("### Valores")
                valor = st.number_input("Valor semanal", min_value=0.0, step=50.0)
                caucao = st.number_input("Caução", min_value=0.0, step=100.0)

                st.markdown("### Vistoria")
                acessorios = st.text_area("Acessórios", value="Conforme vistoria")
                estado_conservacao = st.text_area("Estado de conservação", value="Veículo em bom estado")
                pintura = st.text_input("Pintura", value="Sem observações")

                tipo_combustivel = st.selectbox("Combustível", ["Flex", "Gasolina", "Etanol", "Diesel"])
                nivel_combustivel = st.selectbox("Nível do tanque", ["Vazio", "1/4", "1/2", "3/4", "Cheio"])

                km_atual = st.number_input("KM atual", min_value=0, step=1)
                km_limite = st.text_input("KM limite mensal", value="5000")
                valor_km = st.text_input("Valor KM excedente", value="0,50")

                gerar = st.form_submit_button("Gerar contrato")

                if gerar:
                    if data_fim < data_inicio:
                        st.error("A data final não pode ser menor que a inicial.")
                    else:
                        semanas_cobradas = calcular_semanas_cobradas(data_inicio, data_fim)
                        valor_total_contrato = valor * semanas_cobradas

                        dados = {
                            "locatario_nome": formatar_nome(cliente["nome"] or ""),
                            "locatario_cpf": formatar_cpf(cliente["cpf"] or ""),
                            "locatario_rg": formatar_rg(cliente["rg"] or ""),
                            "locatario_endereco": endereco,
                            "locatario_cidade": cidade,
                            "locatario_estado": estado.strip().upper(),
                            "locatario_cep": formatar_cep(cep),
                            "veiculo_modelo": veiculo["modelo"] or "",
                            "veiculo_placa": veiculo["placa"] or "",
                            "veiculo_ano": veiculo["ano"] or "",
                            "veiculo_cor": veiculo["cor"] or "",
                            "valor": formatar_moeda(valor),
                            "valor_extenso": valor_por_extenso(valor),
                            "data_inicio": data_inicio.strftime("%d/%m/%Y"),
                            "data_fim": data_fim.strftime("%d/%m/%Y"),
                            "duracao": duracao_texto(data_inicio, data_fim),
                            "data_assinatura_extenso": data_por_extenso(datetime.now()),
                            "cidade": cidade,
                            "acessorios": acessorios,
                            "estado_conservacao": estado_conservacao,
                            "pintura": pintura,
                            "tipo_combustivel": tipo_combustivel,
                            "nivel_combustivel": nivel_combustivel,
                            "km_atual": km_atual,
                            "km_limite": km_limite,
                            "valor_km_excedente": valor_km,
                        }

                        arquivo, erro = gerar_contrato_docx(dados)

                        if erro:
                            st.error(erro)
                        else:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO contratos (
                                    cliente_id, veiculo_id, data_inicio, data_fim,
                                    valor_semanal, valor_total_contrato, caucao, status,
                                    arquivo_contrato, valor_pago, status_pagamento, data_pagamento, comprovante_pagamento
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    cliente_id,
                                    veiculo_id,
                                    str(data_inicio),
                                    str(data_fim),
                                    valor,
                                    valor_total_contrato,
                                    caucao,
                                    "Ativo",
                                    arquivo,
                                    0,
                                    "Pendente",
                                    None,
                                    None,
                                ),
                            )

                            cursor.execute("""
                                UPDATE veiculos
                                SET status = 'Alugado'
                                WHERE id = ?
                            """, (veiculo_id,))

                            conn.commit()

                            st.session_state.arquivo_contrato_gerado = arquivo
                            st.session_state.nome_arquivo_contrato_gerado = os.path.basename(arquivo)

                            st.success("Contrato gerado com sucesso.")
                            st.info(
                                f"Semanas cobradas: {semanas_cobradas} | "
                                f"Valor total do contrato: R$ {valor_total_contrato:.2f}"
                            )

            if (
                st.session_state.arquivo_contrato_gerado
                and os.path.exists(st.session_state.arquivo_contrato_gerado)
            ):
                st.markdown("### Download do contrato recém-gerado")
                with open(st.session_state.arquivo_contrato_gerado, "rb") as f:
                    st.download_button(
                        "Baixar contrato em Word",
                        data=f,
                        file_name=st.session_state.nome_arquivo_contrato_gerado,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

    with tab2:
        df = pd.read_sql_query(
            """
            SELECT
                contratos.id,
                contratos.veiculo_id,
                clientes.nome AS cliente,
                veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
                contratos.data_inicio,
                contratos.data_fim,
                contratos.valor_semanal,
                contratos.valor_total_contrato,
                contratos.valor_pago,
                contratos.status_pagamento,
                contratos.data_pagamento,
                contratos.comprovante_pagamento,
                contratos.caucao,
                contratos.status,
                contratos.arquivo_contrato
            FROM contratos
            INNER JOIN clientes ON contratos.cliente_id = clientes.id
            INNER JOIN veiculos ON contratos.veiculo_id = veiculos.id
            ORDER BY contratos.id DESC
            """,
            conn,
        )

        if df.empty:
            st.info("Nenhum contrato ainda.")
        else:
            st.dataframe(
                df.drop(columns=["veiculo_id"]),
                use_container_width=True
            )

            st.divider()
            st.markdown("### Alertas de comprovantes")

            df_sem_comprovante = df[
                (
                    df["status_pagamento"].isin(["Pago", "Parcial", "Pendente"])
                ) & (
                    df["comprovante_pagamento"].isna()
                    | (df["comprovante_pagamento"] == "")
                )
            ].copy()

            if df_sem_comprovante.empty:
                st.success("Todos os contratos possuem comprovante ou ainda não exigem atenção.")
            else:
                pagos_sem = df_sem_comprovante[df_sem_comprovante["status_pagamento"] == "Pago"]
                parciais_sem = df_sem_comprovante[df_sem_comprovante["status_pagamento"] == "Parcial"]
                pendentes_sem = df_sem_comprovante[df_sem_comprovante["status_pagamento"] == "Pendente"]

                c1, c2, c3 = st.columns(3)
                c1.metric("Pagos sem comprovante", len(pagos_sem))
                c2.metric("Parciais sem comprovante", len(parciais_sem))
                c3.metric("Pendentes sem comprovante", len(pendentes_sem))

                if not pagos_sem.empty:
                    st.error("Existem contratos marcados como pagos sem comprovante anexado.")
                    st.dataframe(
                        pagos_sem[[
                            "id", "cliente", "veiculo", "valor_total_contrato",
                            "valor_pago", "status_pagamento", "data_pagamento", "status"
                        ]],
                        use_container_width=True
                    )

                if not parciais_sem.empty:
                    st.warning("Existem contratos parciais sem comprovante anexado.")
                    st.dataframe(
                        parciais_sem[[
                            "id", "cliente", "veiculo", "valor_total_contrato",
                            "valor_pago", "status_pagamento", "data_pagamento", "status"
                        ]],
                        use_container_width=True
                    )

                if not pendentes_sem.empty:
                    st.info("Existem contratos pendentes sem comprovante.")
                    st.dataframe(
                        pendentes_sem[[
                            "id", "cliente", "veiculo", "valor_total_contrato",
                            "valor_pago", "status_pagamento", "data_pagamento", "status"
                        ]],
                        use_container_width=True
                    )

            st.divider()
            st.markdown("### Baixar contrato salvo")

            opcoes_download = {
                f"Contrato #{row['id']} - {row['cliente']} - {row['veiculo']}": row["id"]
                for _, row in df.iterrows()
            }

            contrato_download_escolhido = st.selectbox(
                "Selecione o contrato para baixar",
                list(opcoes_download.keys()),
                key="baixar_contrato_existente"
            )

            contrato_download_id = opcoes_download[contrato_download_escolhido]
            registro_download = df[df["id"] == contrato_download_id].iloc[0]
            caminho_arquivo = registro_download["arquivo_contrato"]

            st.write(f"**Cliente:** {registro_download['cliente']}")
            st.write(f"**Veículo:** {registro_download['veiculo']}")
            st.write(f"**Status contrato:** {registro_download['status']}")
            st.write(f"**Status pagamento:** {registro_download['status_pagamento']}")

            if caminho_arquivo and os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, "rb") as f:
                    st.download_button(
                        "Baixar contrato selecionado",
                        data=f,
                        file_name=os.path.basename(caminho_arquivo),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"download_contrato_{contrato_download_id}"
                    )
            else:
                st.warning("Arquivo do contrato não encontrado no sistema.")

            st.divider()
            st.markdown("### Atualizar pagamento do contrato")

            opcoes_pagamento = {
                f"Contrato #{row['id']} - {row['cliente']} - {row['veiculo']}": row["id"]
                for _, row in df.iterrows()
            }

            contrato_pagamento_escolhido = st.selectbox(
                "Selecione o contrato para atualizar pagamento",
                list(opcoes_pagamento.keys()),
                key="contrato_pagamento_select"
            )

            contrato_pagamento_id = opcoes_pagamento[contrato_pagamento_escolhido]
            registro_pagamento = df[df["id"] == contrato_pagamento_id].iloc[0]

            with st.form("form_pagamento_contrato"):
                valor_pago = st.number_input(
                    "Valor pago",
                    min_value=0.0,
                    value=float(registro_pagamento["valor_pago"] or 0),
                    step=50.0
                )

                status_pagamento = st.selectbox(
                    "Status do pagamento",
                    ["Pendente", "Parcial", "Pago"],
                    index=["Pendente", "Parcial", "Pago"].index(
                        registro_pagamento["status_pagamento"]
                        if registro_pagamento["status_pagamento"] in ["Pendente", "Parcial", "Pago"]
                        else "Pendente"
                    )
                )

                data_pagamento = st.date_input("Data do pagamento")

                comprovante = st.file_uploader(
                    "Comprovante de pagamento",
                    type=["jpg", "jpeg", "png", "pdf", "doc", "docx"],
                    key=f"comprovante_{contrato_pagamento_id}"
                )

                salvar_pagamento = st.form_submit_button("Salvar pagamento")

                if salvar_pagamento:
                    comprovante_path = None
                    if comprovante is not None:
                        comprovante_path = salvar_comprovante(contrato_pagamento_id, comprovante)

                    atualizar_pagamento(
                        contrato_pagamento_id,
                        valor_pago,
                        status_pagamento,
                        str(data_pagamento),
                        comprovante_path
                    )
                    st.success("Pagamento atualizado com sucesso.")
                    st.rerun()

            st.write(
                f"**Comprovante atual:** "
                f"{registro_pagamento['comprovante_pagamento'] or 'Nenhum arquivo enviado'}"
            )

            caminho_comprovante = registro_pagamento["comprovante_pagamento"]
            if caminho_comprovante and os.path.exists(caminho_comprovante):
                with open(caminho_comprovante, "rb") as f:
                    st.download_button(
                        "Baixar comprovante atual",
                        data=f,
                        file_name=os.path.basename(caminho_comprovante),
                        use_container_width=True,
                        key=f"download_comprovante_{contrato_pagamento_id}"
                    )

            st.divider()
            st.markdown("### Finalizar contrato")

            contratos_ativos = df[df["status"] == "Ativo"]

            if contratos_ativos.empty:
                st.info("Não há contratos ativos para finalizar.")
            else:
                opcoes_contrato = {
                    f"Contrato #{row['id']} - {row['cliente']} - {row['veiculo']}": row["id"]
                    for _, row in contratos_ativos.iterrows()
                }

                contrato_escolhido = st.selectbox(
                    "Selecione o contrato ativo",
                    list(opcoes_contrato.keys()),
                    key="finalizar_contrato_select"
                )

                contrato_id = opcoes_contrato[contrato_escolhido]

                if st.button("Finalizar contrato selecionado", type="primary"):
                    sucesso, mensagem = finalizar_contrato(contrato_id)

                    if sucesso:
                        st.success(mensagem)
                        st.rerun()
                    else:
                        st.warning(mensagem)

    conn.close()