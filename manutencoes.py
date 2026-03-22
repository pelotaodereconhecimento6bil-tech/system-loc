import os
from datetime import datetime

import pandas as pd
import streamlit as st
from database import conectar


PASTA_FOTOS_MANUTENCOES = "fotos_manutencoes"


def salvar_foto_manutencao(foto, veiculo_texto):
    if foto is None:
        return ""

    os.makedirs(PASTA_FOTOS_MANUTENCOES, exist_ok=True)

    nome_base = veiculo_texto.replace(" ", "_").replace("-", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extensao = os.path.splitext(foto.name)[1].lower()

    if not extensao:
        extensao = ".jpg"

    nome_arquivo = f"manutencao_{nome_base}_{timestamp}{extensao}"
    caminho_arquivo = os.path.join(PASTA_FOTOS_MANUTENCOES, nome_arquivo)

    with open(caminho_arquivo, "wb") as f:
        f.write(foto.getbuffer())

    return caminho_arquivo


def classificar_alerta(km_atual, km_limite):
    if not km_limite or km_limite <= 0:
        return None
    diferenca = km_limite - km_atual
    if diferenca < 0:
        return "vencido"
    if diferenca <= 500:
        return "urgente"
    if diferenca <= 1500:
        return "proximo"
    return None


def mostrar_alerta_item(nome, km_atual, km_limite):
    status = classificar_alerta(km_atual, km_limite)

    if status == "vencido":
        st.error(f"{nome}: vencido. Atual: {km_atual} km | Limite: {km_limite} km")
    elif status == "urgente":
        st.warning(f"{nome}: atenção. Atual: {km_atual} km | Limite: {km_limite} km")
    elif status == "proximo":
        st.info(f"{nome}: se aproximando. Atual: {km_atual} km | Limite: {km_limite} km")


def tela_manutencoes():
    st.subheader("Manutenções")

    conn = conectar()
    veiculos = pd.read_sql_query(
        "SELECT id, modelo, placa FROM veiculos ORDER BY modelo",
        conn
    )

    if veiculos.empty:
        st.info("Cadastre veículos antes de registrar manutenções.")
        conn.close()
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Nova manutenção", "Histórico", "Checklist preventivo", "Editar", "Excluir"]
    )

    with tab1:
        with st.form("form_manutencao"):
            opcoes = {
                f"{row['modelo']} - {row['placa']}": row["id"]
                for _, row in veiculos.iterrows()
            }

            veiculo_escolhido = st.selectbox("Veículo", list(opcoes.keys()))
            data_manutencao = st.date_input("Data da manutenção")
            tipo_servico = st.text_input("Tipo de serviço")
            descricao = st.text_area("Descrição")
            valor = st.number_input("Valor", min_value=0.0, step=50.0)
            oficina = st.text_input("Oficina ou responsável")
            km_atual = st.number_input("KM atual", min_value=0, step=1)

            st.markdown("### Próximos controles preventivos")
            proxima_troca_oleo = st.number_input("Próxima troca de óleo (KM)", min_value=0, step=500)
            km_prox_revisao = st.number_input("Próxima revisão (KM)", min_value=0, step=500)
            km_prox_pneu = st.number_input("Próxima troca de pneus (KM)", min_value=0, step=500)
            km_prox_freio = st.number_input("Próxima revisão de freio (KM)", min_value=0, step=500)
            km_prox_bateria = st.number_input("Próxima troca de bateria (KM)", min_value=0, step=500)

            observacoes = st.text_area("Observações adicionais")
            foto = st.file_uploader("Foto da manutenção/peça/serviço", type=["jpg", "jpeg", "png", "webp"])

            salvar = st.form_submit_button("Salvar manutenção")

            if salvar:
                veiculo_id = opcoes[veiculo_escolhido]
                foto_path = salvar_foto_manutencao(foto, veiculo_escolhido)

                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO manutencoes (
                        veiculo_id, data_manutencao, tipo_servico, descricao,
                        valor, oficina, km_atual, proxima_troca_oleo,
                        observacoes, foto_path, km_prox_revisao,
                        km_prox_pneu, km_prox_freio, km_prox_bateria
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    veiculo_id,
                    str(data_manutencao),
                    tipo_servico,
                    descricao,
                    valor,
                    oficina,
                    km_atual,
                    proxima_troca_oleo,
                    observacoes,
                    foto_path,
                    km_prox_revisao,
                    km_prox_pneu,
                    km_prox_freio,
                    km_prox_bateria
                ))
                conn.commit()
                st.success("Manutenção registrada com sucesso.")
                st.rerun()

    df = pd.read_sql_query("""
        SELECT
            manutencoes.id,
            manutencoes.veiculo_id,
            veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
            manutencoes.data_manutencao,
            manutencoes.tipo_servico,
            manutencoes.descricao,
            manutencoes.valor,
            manutencoes.oficina,
            manutencoes.km_atual,
            manutencoes.proxima_troca_oleo,
            manutencoes.km_prox_revisao,
            manutencoes.km_prox_pneu,
            manutencoes.km_prox_freio,
            manutencoes.km_prox_bateria,
            manutencoes.observacoes,
            manutencoes.foto_path
        FROM manutencoes
        INNER JOIN veiculos ON manutencoes.veiculo_id = veiculos.id
        ORDER BY manutencoes.id DESC
    """, conn)

    with tab2:
        if df.empty:
            st.info("Nenhuma manutenção cadastrada ainda.")
        else:
            st.dataframe(df.drop(columns=["foto_path", "veiculo_id"]), use_container_width=True)

            st.divider()
            st.markdown("### Visualizar foto da manutenção")

            opcoes_manutencao = {
                f"Manutenção #{row['id']} - {row['veiculo']} - {row['data_manutencao']}": row["id"]
                for _, row in df.iterrows()
            }

            manutencao_escolhida = st.selectbox("Selecione a manutenção", list(opcoes_manutencao.keys()))
            manutencao_id = opcoes_manutencao[manutencao_escolhida]
            registro = df[df["id"] == manutencao_id].iloc[0]

            st.write(f"**Veículo:** {registro['veiculo']}")
            st.write(f"**Data:** {registro['data_manutencao']}")
            st.write(f"**Tipo de serviço:** {registro['tipo_servico']}")
            st.write(f"**Descrição:** {registro['descricao']}")
            st.write(f"**Valor:** R$ {registro['valor']:.2f}")
            st.write(f"**Oficina:** {registro['oficina']}")
            st.write(f"**KM atual:** {registro['km_atual']}")
            st.write(f"**Próxima troca de óleo:** {registro['proxima_troca_oleo']}")
            st.write(f"**Próxima revisão:** {registro['km_prox_revisao']}")
            st.write(f"**Próxima troca de pneus:** {registro['km_prox_pneu']}")
            st.write(f"**Próximo freio:** {registro['km_prox_freio']}")
            st.write(f"**Próxima bateria:** {registro['km_prox_bateria']}")
            st.write(f"**Observações:** {registro['observacoes']}")

            if registro["foto_path"] and os.path.exists(registro["foto_path"]):
                st.image(registro["foto_path"], caption="Foto da manutenção", width=320)
            else:
                st.info("Esta manutenção não possui foto cadastrada.")

    with tab3:
        st.subheader("Checklist Preventivo")

        ultimas_manutencoes = pd.read_sql_query("""
            SELECT m.*
            FROM manutencoes m
            INNER JOIN (
                SELECT veiculo_id, MAX(id) AS ultimo_id
                FROM manutencoes
                GROUP BY veiculo_id
            ) ult
            ON m.id = ult.ultimo_id
        """, conn)

        if ultimas_manutencoes.empty:
            st.info("Nenhuma manutenção registrada ainda para gerar checklist.")
        else:
            veiculos_df = pd.read_sql_query("""
                SELECT id, modelo, placa
                FROM veiculos
                ORDER BY modelo
            """, conn)

            checklist = ultimas_manutencoes.merge(
                veiculos_df,
                left_on="veiculo_id",
                right_on="id",
                suffixes=("", "_veiculo")
            )

            opcoes_checklist = {
                f"{row['modelo']} - {row['placa']}": row["veiculo_id"]
                for _, row in checklist.iterrows()
            }

            veiculo_check = st.selectbox("Selecione o veículo", list(opcoes_checklist.keys()), key="checklist_veiculo")
            veiculo_id_check = opcoes_checklist[veiculo_check]
            registro = checklist[checklist["veiculo_id"] == veiculo_id_check].iloc[0]

            st.write(f"**Veículo:** {registro['modelo']} - {registro['placa']}")
            st.write(f"**KM atual de referência:** {registro['km_atual']}")

            mostrar_alerta_item("Troca de óleo", registro["km_atual"], registro["proxima_troca_oleo"])
            mostrar_alerta_item("Revisão", registro["km_atual"], registro["km_prox_revisao"])
            mostrar_alerta_item("Pneus", registro["km_atual"], registro["km_prox_pneu"])
            mostrar_alerta_item("Freios", registro["km_atual"], registro["km_prox_freio"])
            mostrar_alerta_item("Bateria", registro["km_atual"], registro["km_prox_bateria"])

    with tab4:
        if df.empty:
            st.info("Nenhuma manutenção cadastrada.")
        else:
            opcoes_editar = {
                f"Manutenção #{row['id']} - {row['veiculo']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a manutenção para editar", list(opcoes_editar.keys()), key="editar_manutencao")
            manutencao_id = opcoes_editar[escolha]
            registro = df[df["id"] == manutencao_id].iloc[0]

            with st.form("form_editar_manutencao"):
                nova_data = st.text_input("Data", value=str(registro["data_manutencao"]))
                novo_tipo = st.text_input("Tipo de serviço", value=registro["tipo_servico"] or "")
                nova_descricao = st.text_area("Descrição", value=registro["descricao"] or "")
                novo_valor = st.number_input("Valor", min_value=0.0, value=float(registro["valor"] or 0), step=50.0)
                nova_oficina = st.text_input("Oficina", value=registro["oficina"] or "")
                novo_km = st.number_input("KM atual", min_value=0, value=int(registro["km_atual"] or 0), step=1)
                novo_oleo = st.number_input("Próxima troca de óleo", min_value=0, value=int(registro["proxima_troca_oleo"] or 0), step=500)
                nova_revisao = st.number_input("Próxima revisão", min_value=0, value=int(registro["km_prox_revisao"] or 0), step=500)
                novo_pneu = st.number_input("Próximo pneu", min_value=0, value=int(registro["km_prox_pneu"] or 0), step=500)
                novo_freio = st.number_input("Próximo freio", min_value=0, value=int(registro["km_prox_freio"] or 0), step=500)
                nova_bateria = st.number_input("Próxima bateria", min_value=0, value=int(registro["km_prox_bateria"] or 0), step=500)
                novas_observacoes = st.text_area("Observações", value=registro["observacoes"] or "")

                salvar_edicao = st.form_submit_button("Salvar alterações")

                if salvar_edicao:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE manutencoes
                        SET data_manutencao = ?, tipo_servico = ?, descricao = ?, valor = ?,
                            oficina = ?, km_atual = ?, proxima_troca_oleo = ?, km_prox_revisao = ?,
                            km_prox_pneu = ?, km_prox_freio = ?, km_prox_bateria = ?, observacoes = ?
                        WHERE id = ?
                    """, (
                        nova_data, novo_tipo, nova_descricao, novo_valor,
                        nova_oficina, novo_km, novo_oleo, nova_revisao,
                        novo_pneu, novo_freio, nova_bateria, novas_observacoes,
                        manutencao_id
                    ))
                    conn.commit()
                    st.success("Manutenção atualizada com sucesso.")
                    st.rerun()

    with tab5:
        if df.empty:
            st.info("Nenhuma manutenção cadastrada.")
        else:
            opcoes_excluir = {
                f"Manutenção #{row['id']} - {row['veiculo']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a manutenção para excluir", list(opcoes_excluir.keys()), key="excluir_manutencao")
            manutencao_id = opcoes_excluir[escolha]

            if st.button("Excluir manutenção", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM manutencoes WHERE id = ?", (manutencao_id,))
                conn.commit()
                st.success("Manutenção excluída com sucesso.")
                st.rerun()

    conn.close()