import os
import json
import base64
import hashlib
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from PIL import Image, ImageDraw
from streamlit_geolocation import streamlit_geolocation
from streamlit_drawable_canvas import st_canvas

from database import conectar
from relatorio_vistoria import gerar_pdf_vistoria


BASE_DIR = "fotos_vistorias"
PASTA_ASSINATURAS = "assinaturas_vistorias"


def obter_endereco_por_coordenadas(latitude, longitude):
    if latitude is None or longitude is None:
        return ""

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
            },
            headers={"User-Agent": "locadora-system-vistoria"},
            timeout=10,
        )
        response.raise_for_status()
        dados = response.json()
        return dados.get("display_name", "")
    except Exception:
        return ""


def buscar_contrato_ativo_do_veiculo(conn, veiculo_id):
    query = """
        SELECT
            contratos.id AS contrato_id,
            clientes.nome AS cliente_nome
        FROM contratos
        INNER JOIN clientes ON clientes.id = contratos.cliente_id
        WHERE contratos.veiculo_id = ?
          AND contratos.status = 'Ativo'
        ORDER BY contratos.id DESC
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn, params=(veiculo_id,))

    if df.empty:
        return None, "Sem contrato ativo"

    return int(df.iloc[0]["contrato_id"]), df.iloc[0]["cliente_nome"]


def gerar_hash_vistoria(dados_hash):
    conteudo = json.dumps(dados_hash, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def quebrar_texto(texto, limite=58):
    if not texto:
        return []

    palavras = texto.split()
    linhas = []
    atual = ""

    for palavra in palavras:
        teste = f"{atual} {palavra}".strip()
        if len(teste) <= limite:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas


def montar_info_legenda(endereco, latitude, longitude, data_hora_real):
    linhas = []

    if endereco:
        linhas.extend(quebrar_texto(f"Local: {endereco}", limite=58))
    else:
        linhas.append("Local: não capturado")

    if latitude is not None and longitude is not None:
        linhas.append(f"Lat: {latitude:.5f} | Lon: {longitude:.5f}")
    else:
        linhas.append("Lat/Lon: não capturado")

    linhas.append(f"Data/Hora: {data_hora_real}")
    return linhas


def salvar_foto(pasta, nome_base, foto, info_linhas=None):
    if foto is None:
        return ""

    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome_base + ".jpg")

    imagem = Image.open(foto).convert("RGB")
    imagem.thumbnail((1200, 1200))

    if info_linhas:
        largura, altura = imagem.size
        linha_altura = 20
        padding = 10
        altura_legenda = (len(info_linhas) * linha_altura) + (padding * 2)

        nova_imagem = Image.new(
            "RGB",
            (largura, altura + altura_legenda),
            "white"
        )

        nova_imagem.paste(imagem, (0, 0))
        draw = ImageDraw.Draw(nova_imagem)

        y_texto = altura + padding
        for linha in info_linhas:
            draw.text((10, y_texto), linha, fill="black")
            y_texto += linha_altura

        nova_imagem.save(caminho, "JPEG", quality=85, optimize=True)
    else:
        imagem.save(caminho, "JPEG", quality=85, optimize=True)

    return caminho


def salvar_assinatura(canvas_result, pasta, nome_base):
    if canvas_result is None or canvas_result.image_data is None:
        return ""

    image_data = canvas_result.image_data
    if image_data is None:
        return ""

    if image_data[:, :, 3].max() == 0:
        return ""

    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"{nome_base}.png")

    img = Image.fromarray((image_data[:, :, :4]).astype("uint8"), mode="RGBA")
    fundo_branco = Image.new("RGBA", img.size, "WHITE")
    fundo_branco.alpha_composite(img)
    fundo_branco.convert("RGB").save(caminho, "PNG")

    return caminho


def mostrar_preview_pdf(caminho_pdf):
    if not caminho_pdf or not os.path.exists(caminho_pdf):
        return

    st.markdown("### Pré-visualização do PDF")

    with open(caminho_pdf, "rb") as f:
        pdf_bytes = f.read()

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="900"
            style="border: 1px solid #ddd; border-radius: 8px;"
        ></iframe>
    """
    st.components.v1.html(pdf_display, height=920, scrolling=True)

    st.download_button(
        "Baixar PDF da vistoria",
        data=pdf_bytes,
        file_name=os.path.basename(caminho_pdf),
        mime="application/pdf",
        use_container_width=True
    )


def inicializar_estado_geo():
    if "geo_latitude" not in st.session_state:
        st.session_state.geo_latitude = None
    if "geo_longitude" not in st.session_state:
        st.session_state.geo_longitude = None
    if "geo_endereco" not in st.session_state:
        st.session_state.geo_endereco = ""
    if "geo_capturada" not in st.session_state:
        st.session_state.geo_capturada = False
    if "ultimo_pdf_vistoria" not in st.session_state:
        st.session_state.ultimo_pdf_vistoria = None
    if "ultima_vistoria_salva" not in st.session_state:
        st.session_state.ultima_vistoria_salva = False
    if "veiculo_vistoria_selecionado" not in st.session_state:
        st.session_state.veiculo_vistoria_selecionado = None


def processar_geolocalizacao(location):
    inicializar_estado_geo()

    if (
        location
        and location.get("latitude") is not None
        and location.get("longitude") is not None
    ):
        nova_lat = float(location["latitude"])
        nova_lon = float(location["longitude"])

        mudou = (
            st.session_state.geo_latitude != nova_lat
            or st.session_state.geo_longitude != nova_lon
        )

        st.session_state.geo_latitude = nova_lat
        st.session_state.geo_longitude = nova_lon
        st.session_state.geo_capturada = True

        if mudou or not st.session_state.geo_endereco:
            st.session_state.geo_endereco = obter_endereco_por_coordenadas(
                nova_lat,
                nova_lon
            )


def tela_vistorias():
    st.subheader("Vistorias")

    conn = conectar()

    veiculos = pd.read_sql_query(
        "SELECT id, modelo, placa FROM veiculos ORDER BY modelo",
        conn
    )

    if veiculos.empty:
        st.info("Cadastre veículos antes de registrar vistorias.")
        conn.close()
        return

    tab1, tab2 = st.tabs(["Nova vistoria", "Histórico"])

    with tab1:
        inicializar_estado_geo()

        if st.session_state.ultima_vistoria_salva:
            st.success("Vistoria concluída com sucesso e salva.")
            st.session_state.ultima_vistoria_salva = False

        st.markdown("### 📍 Localização")
        st.caption(
            "No celular, permita o acesso ao GPS. "
            "Se não capturar, a vistoria ainda poderá ser salva sem localização."
        )

        location = streamlit_geolocation()
        processar_geolocalizacao(location)

        latitude = st.session_state.geo_latitude
        longitude = st.session_state.geo_longitude
        endereco = st.session_state.geo_endereco

        col_geo1, col_geo2 = st.columns(2)

        with col_geo1:
            if st.button("Atualizar localização", use_container_width=True):
                st.rerun()

        with col_geo2:
            if st.button("Limpar localização", use_container_width=True):
                st.session_state.geo_latitude = None
                st.session_state.geo_longitude = None
                st.session_state.geo_endereco = ""
                st.session_state.geo_capturada = False
                st.rerun()

        if latitude is not None and longitude is not None:
            st.success("Localização capturada.")
            st.write(f"Latitude: {latitude:.6f}")
            st.write(f"Longitude: {longitude:.6f}")
            st.write(f"Endereço: {endereco or 'Endereço não encontrado'}")
        else:
            st.warning(
                "Localização não capturada. "
                "A vistoria poderá ser salva mesmo assim."
            )

        opcoes = {
            f"{row['modelo']} - {row['placa']}": row["id"]
            for _, row in veiculos.iterrows()
        }

        st.markdown("### Dados da vistoria")
        veiculo_nome = st.selectbox("Veículo", list(opcoes.keys()), key="veiculo_vistoria_select")
        veiculo_id = opcoes[veiculo_nome]

        contrato_id, cliente_contrato = buscar_contrato_ativo_do_veiculo(conn, veiculo_id)

        st.info(f"Cliente do contrato ativo: {cliente_contrato}")
        vistoriador = st.text_input("Nome do vistoriador")

        with st.form("form_vistoria"):
            data_vistoria = st.date_input("Data")
            odometro = st.number_input("Odômetro", min_value=0, step=1)
            observacoes = st.text_area("Observações gerais")

            st.markdown("### Fotos principais (opcional)")

            foto_frente = st.file_uploader("Frente", type=["jpg", "jpeg", "png", "webp"], key="foto_frente")
            foto_motor = st.file_uploader("Motor", type=["jpg", "jpeg", "png", "webp"], key="foto_motor")
            foto_lat_esq = st.file_uploader("Lateral esquerda", type=["jpg", "jpeg", "png", "webp"], key="foto_lat_esq")
            foto_traseira = st.file_uploader("Traseira", type=["jpg", "jpeg", "png", "webp"], key="foto_traseira")
            foto_lat_dir = st.file_uploader("Lateral direita", type=["jpg", "jpeg", "png", "webp"], key="foto_lat_dir")
            foto_hodometro = st.file_uploader("Hodômetro", type=["jpg", "jpeg", "png", "webp"], key="foto_hodometro")

            st.markdown("### Fotos de observação (até 4)")
            obs_1_foto = st.file_uploader("Foto observação 1", type=["jpg", "jpeg", "png", "webp"], key="obs_1_foto")
            obs_1_texto = st.text_input("Descrição observação 1")

            obs_2_foto = st.file_uploader("Foto observação 2", type=["jpg", "jpeg", "png", "webp"], key="obs_2_foto")
            obs_2_texto = st.text_input("Descrição observação 2")

            obs_3_foto = st.file_uploader("Foto observação 3", type=["jpg", "jpeg", "png", "webp"], key="obs_3_foto")
            obs_3_texto = st.text_input("Descrição observação 3")

            obs_4_foto = st.file_uploader("Foto observação 4", type=["jpg", "jpeg", "png", "webp"], key="obs_4_foto")
            obs_4_texto = st.text_input("Descrição observação 4")

            st.markdown("### Assinatura do cliente")
            st.caption("Use a área abaixo para o cliente assinar com o dedo no celular.")
            st.info("A assinatura aparece logo abaixo do formulário. Depois clique em salvar.")

            salvar = st.form_submit_button("Salvar vistoria")

        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 1)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=180,
            width=600,
            drawing_mode="freedraw",
            key="assinatura_canvas_vistoria",
            display_toolbar=True,
            update_streamlit=False,
        )

        col_ass1, col_ass2 = st.columns(2)
        with col_ass1:
            if st.button("Limpar assinatura", use_container_width=True):
                st.rerun()
        with col_ass2:
            st.caption("Se preferir, a vistoria também pode ser salva sem assinatura.")

        if salvar:
            latitude = st.session_state.geo_latitude
            longitude = st.session_state.geo_longitude
            endereco = st.session_state.geo_endereco

            data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_hora_real = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            info_linhas = montar_info_legenda(
                endereco=endereco,
                latitude=latitude,
                longitude=longitude,
                data_hora_real=data_hora_real,
            )

            pasta = os.path.join(
                BASE_DIR,
                veiculo_nome.replace(" ", "_").replace("/", "_"),
                data_str
            )

            principais = {
                "frente": salvar_foto(pasta, "frente", foto_frente, info_linhas),
                "motor": salvar_foto(pasta, "motor", foto_motor, info_linhas),
                "lateral_esquerda": salvar_foto(pasta, "lateral_esquerda", foto_lat_esq, info_linhas),
                "traseira": salvar_foto(pasta, "traseira", foto_traseira, info_linhas),
                "lateral_direita": salvar_foto(pasta, "lateral_direita", foto_lat_dir, info_linhas),
                "hodometro": salvar_foto(pasta, "hodometro", foto_hodometro, info_linhas),
            }

            observacoes_fotos = []

            if obs_1_foto is not None:
                caminho = salvar_foto(pasta, "obs_1", obs_1_foto, info_linhas)
                observacoes_fotos.append({"foto": caminho, "descricao": obs_1_texto})

            if obs_2_foto is not None:
                caminho = salvar_foto(pasta, "obs_2", obs_2_foto, info_linhas)
                observacoes_fotos.append({"foto": caminho, "descricao": obs_2_texto})

            if obs_3_foto is not None:
                caminho = salvar_foto(pasta, "obs_3", obs_3_foto, info_linhas)
                observacoes_fotos.append({"foto": caminho, "descricao": obs_3_texto})

            if obs_4_foto is not None:
                caminho = salvar_foto(pasta, "obs_4", obs_4_foto, info_linhas)
                observacoes_fotos.append({"foto": caminho, "descricao": obs_4_texto})

            assinatura_path = salvar_assinatura(
                canvas_result=canvas_result,
                pasta=PASTA_ASSINATURAS,
                nome_base=f"assinatura_{veiculo_id}_{data_str}"
            )

            foto_path_dict = {
                "principais": principais,
                "observacoes_fotos": observacoes_fotos,
                "assinatura_cliente": assinatura_path
            }
            foto_path = json.dumps(foto_path_dict, ensure_ascii=False)

            dados_hash = {
                "veiculo_id": veiculo_id,
                "veiculo_nome": veiculo_nome,
                "contrato_id": contrato_id,
                "cliente_contrato": cliente_contrato,
                "vistoriador": vistoriador,
                "data_vistoria": str(data_vistoria),
                "odometro": odometro,
                "observacoes": observacoes,
                "latitude": latitude,
                "longitude": longitude,
                "endereco": endereco,
                "data_hora_real": data_hora_real,
                "fotos": foto_path_dict,
            }
            hash_vistoria = gerar_hash_vistoria(dados_hash)

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vistorias (
                    veiculo_id, contrato_id, cliente_contrato, vistoriador,
                    data_vistoria, odometro, observacoes, foto_path,
                    latitude, longitude, endereco, data_hora_real, hash_vistoria
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                veiculo_id,
                contrato_id,
                cliente_contrato,
                vistoriador,
                str(data_vistoria),
                odometro,
                observacoes,
                foto_path,
                latitude,
                longitude,
                endereco,
                data_hora_real,
                hash_vistoria
            ))

            conn.commit()
            vistoria_id = cursor.lastrowid

            registro_pdf = {
                "id": vistoria_id,
                "veiculo": veiculo_nome,
                "contrato_id": contrato_id,
                "cliente_contrato": cliente_contrato,
                "vistoriador": vistoriador,
                "data_vistoria": str(data_vistoria),
                "odometro": odometro,
                "observacoes": observacoes,
                "latitude": latitude,
                "longitude": longitude,
                "endereco": endereco,
                "data_hora_real": data_hora_real,
                "hash_vistoria": hash_vistoria,
            }

            pasta_pdf = "relatorios_vistorias"
            os.makedirs(pasta_pdf, exist_ok=True)
            nome_pdf = f"vistoria_{vistoria_id}.pdf"
            caminho_pdf = os.path.join(pasta_pdf, nome_pdf)

            dados_pdf = {
                "principais": principais,
                "observacoes_fotos": observacoes_fotos,
                "assinatura_cliente": assinatura_path
            }

            gerar_pdf_vistoria(registro_pdf, dados_pdf, caminho_pdf)

            st.session_state.ultimo_pdf_vistoria = caminho_pdf
            st.session_state.ultima_vistoria_salva = True
            st.rerun()

        if st.session_state.ultimo_pdf_vistoria:
            mostrar_preview_pdf(st.session_state.ultimo_pdf_vistoria)

    with tab2:
        df = pd.read_sql_query("""
            SELECT
                vistorias.id,
                vistorias.contrato_id,
                vistorias.cliente_contrato,
                vistorias.vistoriador,
                vistorias.hash_vistoria,
                veiculos.modelo || ' - ' || veiculos.placa AS veiculo,
                vistorias.data_vistoria,
                vistorias.odometro,
                vistorias.observacoes,
                vistorias.foto_path,
                vistorias.latitude,
                vistorias.longitude,
                vistorias.endereco,
                vistorias.data_hora_real
            FROM vistorias
            INNER JOIN veiculos ON vistorias.veiculo_id = veiculos.id
            ORDER BY vistorias.id DESC
        """, conn)

        if df.empty:
            st.info("Nenhuma vistoria ainda.")
        else:
            st.dataframe(df.drop(columns=["foto_path"]), use_container_width=True)

            st.divider()
            st.markdown("### Visualizar fotos da vistoria")

            opcoes = {
                f"Vistoria #{row['id']} - {row['veiculo']} - {row['data_vistoria']}": row["id"]
                for _, row in df.iterrows()
            }

            escolha = st.selectbox("Selecione a vistoria", list(opcoes.keys()))
            registro = df[df["id"] == opcoes[escolha]].iloc[0]

            st.write(f"**Veículo:** {registro['veiculo']}")
            st.write(f"**Contrato ID:** {registro['contrato_id'] if pd.notna(registro['contrato_id']) else '-'}")
            st.write(f"**Cliente do contrato:** {registro['cliente_contrato'] or 'Sem contrato ativo'}")
            st.write(f"**Vistoriador:** {registro['vistoriador'] or '-'}")
            st.write(f"**Data:** {registro['data_vistoria']}")
            st.write(f"**Data/Hora real:** {registro['data_hora_real'] or '-'}")
            st.write(f"**Odômetro:** {registro['odometro']}")
            st.write(f"**Endereço:** {registro['endereco'] or 'Não capturado'}")
            st.write(f"**Hash de segurança:** `{registro['hash_vistoria'] or '-'}`")

            if pd.notna(registro["latitude"]) and pd.notna(registro["longitude"]):
                st.write(f"**Coordenadas:** {registro['latitude']}, {registro['longitude']}")
                st.link_button(
                    "Abrir no Google Maps",
                    f"https://www.google.com/maps?q={registro['latitude']},{registro['longitude']}",
                    use_container_width=True
                )
            else:
                st.write("**Coordenadas:** não capturadas")

            st.write(f"**Observações gerais:** {registro['observacoes']}")

            dados = {"principais": {}, "observacoes_fotos": [], "assinatura_cliente": ""}
            if registro["foto_path"]:
                try:
                    dados = json.loads(registro["foto_path"])
                except Exception:
                    dados = {"principais": {}, "observacoes_fotos": [], "assinatura_cliente": ""}

            st.markdown("### Fotos principais")
            principais = dados.get("principais", {})
            exibiu_principal = False

            for nome, caminho in principais.items():
                if caminho and os.path.exists(caminho):
                    st.image(caminho, caption=nome.replace("_", " ").title(), width=320)
                    exibiu_principal = True

            if not exibiu_principal:
                st.info("Nenhuma foto principal cadastrada nesta vistoria.")

            st.markdown("### Fotos de observação")
            observacoes_fotos = dados.get("observacoes_fotos", [])
            if observacoes_fotos:
                for i, item in enumerate(observacoes_fotos, start=1):
                    caminho = item.get("foto", "")
                    descricao = item.get("descricao", "")

                    st.markdown(f"**Observação {i}**")
                    st.write(f"Descrição: {descricao or 'sem descrição informada.'}")

                    if caminho and os.path.exists(caminho):
                        st.image(caminho, width=320)
                    else:
                        st.warning("Imagem não encontrada.")
            else:
                st.info("Nenhuma foto de observação cadastrada nesta vistoria.")

            assinatura = dados.get("assinatura_cliente", "")
            st.markdown("### Assinatura do cliente")
            if assinatura and os.path.exists(assinatura):
                st.image(assinatura, width=320)
            else:
                st.info("Esta vistoria não possui assinatura do cliente.")

            st.divider()

            if st.button("Gerar PDF da vistoria"):
                pasta_pdf = "relatorios_vistorias"
                os.makedirs(pasta_pdf, exist_ok=True)

                nome_pdf = f"vistoria_{registro['id']}.pdf"
                caminho_pdf = os.path.join(pasta_pdf, nome_pdf)

                gerar_pdf_vistoria(registro.to_dict(), dados, caminho_pdf)
                st.success("PDF gerado com sucesso.")
                mostrar_preview_pdf(caminho_pdf)

    conn.close()