import os
import qrcode

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def valor_registro(registro, campo, padrao="-"):
    try:
        valor = registro[campo]
        if valor is None or valor == "":
            return padrao
        return valor
    except Exception:
        return padrao


def formatar_texto_quebra(texto, estilo=None):
    estilos = getSampleStyleSheet()

    if estilo is None:
        estilo = estilos["BodyText"]

    if not texto or texto == "-":
        texto = "-"

    texto = str(texto).replace("\n", "<br/>")
    return Paragraph(texto, estilo)


def criar_bloco_foto(caminho, titulo="", descricao=""):
    estilos = getSampleStyleSheet()
    elementos = []

    if titulo:
        elementos.append(Paragraph(f"<b>{titulo}</b>", estilos["BodyText"]))

    if descricao:
        elementos.append(formatar_texto_quebra(descricao, estilos["BodyText"]))

    if caminho and os.path.exists(caminho):
        elementos.append(RLImage(caminho, width=220, height=180))
    else:
        elementos.append(Paragraph("Imagem não encontrada.", estilos["BodyText"]))

    return elementos


def gerar_tabela_duas_colunas(blocos):
    linhas = []
    linha_atual = []

    for bloco in blocos:
        linha_atual.append(bloco)
        if len(linha_atual) == 2:
            linhas.append(linha_atual)
            linha_atual = []

    if linha_atual:
        linha_atual.append("")
        linhas.append(linha_atual)

    tabela = Table(linhas, colWidths=[255, 255])
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.whitesmoke),
    ]))
    return tabela


def gerar_qr_vistoria(registro, caminho_qr):
    latitude = valor_registro(registro, "latitude", "Não capturada")
    longitude = valor_registro(registro, "longitude", "Não capturada")
    endereco = valor_registro(registro, "endereco", "Não capturado")
    data_hora_real = valor_registro(registro, "data_hora_real", "-")

    conteudo = (
        f"VISTORIA #{valor_registro(registro, 'id', '-')}\n"
        f"Veículo: {valor_registro(registro, 'veiculo', '-')}\n"
        f"Contrato ID: {valor_registro(registro, 'contrato_id', '-')}\n"
        f"Cliente do contrato: {valor_registro(registro, 'cliente_contrato', '-')}\n"
        f"Vistoriador: {valor_registro(registro, 'vistoriador', '-')}\n"
        f"Data: {valor_registro(registro, 'data_vistoria', '-')}\n"
        f"Data/Hora real: {data_hora_real}\n"
        f"Odômetro: {valor_registro(registro, 'odometro', '-')}\n"
        f"Endereço: {endereco}\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}\n"
        f"Hash: {valor_registro(registro, 'hash_vistoria', '-')}"
    )

    img_qr = qrcode.make(conteudo)
    img_qr.save(caminho_qr)


def gerar_pdf_vistoria(registro, dados_fotos, caminho_pdf):
    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28,
    )

    estilos = getSampleStyleSheet()

    estilo_obs = ParagraphStyle(
        "obs_custom",
        parent=estilos["BodyText"],
        alignment=TA_LEFT,
        leading=15,
        spaceAfter=6,
    )

    estilo_subtitulo = ParagraphStyle(
        "subtitulo_custom",
        parent=estilos["BodyText"],
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=4,
    )

    estilo_tabela = ParagraphStyle(
        "tabela_quebra",
        parent=estilos["BodyText"],
        alignment=TA_LEFT,
        leading=14,
        wordWrap="CJK",
    )

    elementos = []

    latitude = valor_registro(registro, "latitude", None)
    longitude = valor_registro(registro, "longitude", None)
    endereco = valor_registro(registro, "endereco", "")
    data_hora_real = valor_registro(registro, "data_hora_real", "-")

    if latitude is not None and longitude is not None:
        coordenadas = f"{latitude}, {longitude}"
        status_localizacao = "Geolocalização capturada"
    else:
        coordenadas = "Não capturadas"
        status_localizacao = "Geolocalização não capturada no momento da vistoria"

    endereco_exibir = endereco if endereco else "Não capturado"

    pasta_qr = "temp_qr"
    os.makedirs(pasta_qr, exist_ok=True)
    caminho_qr = os.path.join(
        pasta_qr,
        f"vistoria_qr_{valor_registro(registro, 'id', 'sem_id')}.png"
    )
    gerar_qr_vistoria(registro, caminho_qr)

    cabecalho_esquerda = [
        Paragraph("RELATÓRIO DE VISTORIA", estilos["Title"]),
        Spacer(1, 4),
        Paragraph(
            "Escaneie o QR Code para visualizar o resumo desta vistoria.",
            estilo_subtitulo
        ),
    ]

    cabecalho = Table(
        [[cabecalho_esquerda, RLImage(caminho_qr, width=82, height=82)]],
        colWidths=[420, 82]
    )
    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elementos.append(cabecalho)
    elementos.append(Spacer(1, 14))

    info_data = [
        ["Vistoria ID:", formatar_texto_quebra(str(valor_registro(registro, "id")), estilo_tabela)],
        ["Veículo:", formatar_texto_quebra(valor_registro(registro, "veiculo"), estilo_tabela)],
        ["Contrato ID:", formatar_texto_quebra(str(valor_registro(registro, "contrato_id")), estilo_tabela)],
        ["Cliente do contrato:", formatar_texto_quebra(valor_registro(registro, "cliente_contrato"), estilo_tabela)],
        ["Vistoriador:", formatar_texto_quebra(valor_registro(registro, "vistoriador"), estilo_tabela)],
        ["Data da vistoria:", formatar_texto_quebra(str(valor_registro(registro, "data_vistoria")), estilo_tabela)],
        ["Data/Hora real:", formatar_texto_quebra(str(data_hora_real), estilo_tabela)],
        ["Odômetro:", formatar_texto_quebra(str(valor_registro(registro, "odometro")), estilo_tabela)],
        ["Endereço:", formatar_texto_quebra(endereco_exibir, estilo_tabela)],
        ["Coordenadas:", formatar_texto_quebra(str(coordenadas), estilo_tabela)],
        ["Status localização:", formatar_texto_quebra(status_localizacao, estilo_tabela)],
        ["Hash de segurança:", formatar_texto_quebra(valor_registro(registro, "hash_vistoria"), estilo_tabela)],
        ["Observações gerais:", formatar_texto_quebra(str(valor_registro(registro, "observacoes")), estilo_tabela)],
    ]

    tabela_info = Table(info_data, colWidths=[135, 365])
    tabela_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabela_info)
    elementos.append(Spacer(1, 16))

    observacoes_gerais = valor_registro(registro, "observacoes", "")
    if observacoes_gerais not in ["", "-"]:
        elementos.append(Paragraph("OBSERVAÇÕES", estilos["Heading2"]))
        elementos.append(formatar_texto_quebra(str(observacoes_gerais), estilo_obs))
        elementos.append(Spacer(1, 10))

    principais = dados_fotos.get("principais", {})
    blocos_principais = []

    for nome, caminho in principais.items():
        if caminho and os.path.exists(caminho):
            bloco = criar_bloco_foto(
                caminho=caminho,
                titulo=nome.replace("_", " ").title()
            )
            blocos_principais.append(bloco)

    if blocos_principais:
        elementos.append(Paragraph("FOTOS PRINCIPAIS", estilos["Heading2"]))
        elementos.append(Spacer(1, 8))
        elementos.append(gerar_tabela_duas_colunas(blocos_principais))
        elementos.append(Spacer(1, 14))

    observacoes_fotos = dados_fotos.get("observacoes_fotos", [])
    blocos_obs = []

    for i, item in enumerate(observacoes_fotos, start=1):
        caminho = item.get("foto", "")
        descricao = item.get("descricao", "")

        if caminho and os.path.exists(caminho):
            bloco = criar_bloco_foto(
                caminho=caminho,
                titulo=f"Observação {i}",
                descricao=descricao or "Sem descrição informada."
            )
            blocos_obs.append(bloco)

    if blocos_obs:
        elementos.append(Paragraph("FOTOS DE OBSERVAÇÃO", estilos["Heading2"]))
        elementos.append(Spacer(1, 8))
        elementos.append(gerar_tabela_duas_colunas(blocos_obs))
        elementos.append(Spacer(1, 12))

    assinatura_cliente = dados_fotos.get("assinatura_cliente", "")
    if assinatura_cliente and os.path.exists(assinatura_cliente):
        elementos.append(Paragraph("ASSINATURA DO CLIENTE", estilos["Heading2"]))
        elementos.append(Spacer(1, 8))
        elementos.append(RLImage(assinatura_cliente, width=220, height=90))
        elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(
        "Este relatório foi gerado pelo sistema interno da locadora e reúne as imagens, assinatura e dados registrados no momento da vistoria.",
        estilos["Italic"]
    ))

    doc.build(elementos)