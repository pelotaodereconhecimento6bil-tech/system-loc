from num2words import num2words
import requests
import re


def buscar_cep(cep):
    cep = cep.replace("-", "").strip()
    cep = re.sub(r"\D", "", cep)

    if len(cep) != 8:
        return None

    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    dados = response.json()

    if "erro" in dados:
        return None

    return {
        "endereco": dados.get("logradouro", ""),
        "cidade": dados.get("localidade", ""),
        "estado": dados.get("uf", "")
    }


def formatar_nome(nome):
    palavras = nome.lower().split()
    excecoes = ["da", "de", "do", "dos", "das", "e"]

    resultado = []
    for p in palavras:
        if p in excecoes:
            resultado.append(p)
        else:
            resultado.append(p.capitalize())

    return " ".join(resultado)


def formatar_cpf(cpf):
    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return cpf

    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_rg(rg):
    rg = re.sub(r"\D", "", rg)

    if len(rg) < 8:
        return rg

    if len(rg) == 8:
        return f"{rg[:2]}.{rg[2:5]}.{rg[5:8]}"

    return f"{rg[:2]}.{rg[2:5]}.{rg[5:8]}-{rg[8:]}"


def formatar_telefone(telefone):
    telefone = re.sub(r"\D", "", telefone)

    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    if len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return telefone


def formatar_placa(placa):
    if not placa:
        return ""
    return placa.strip().upper()


def formatar_cep(cep):
    cep = re.sub(r"\D", "", cep)

    if len(cep) == 8:
        return f"{cep[:5]}-{cep[5:]}"
    return cep


def formatar_moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def valor_por_extenso(valor):
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))

    extenso = num2words(inteiro, lang="pt_BR").upper() + " REAIS"

    if centavos > 0:
        extenso += f" E {num2words(centavos, lang='pt_BR').upper()} CENTAVOS"

    return extenso


def data_por_extenso(data_obj):
    meses = [
        "janeiro", "fevereiro", "março", "abril",
        "maio", "junho", "julho", "agosto",
        "setembro", "outubro", "novembro", "dezembro"
    ]

    dia = data_obj.day
    mes = meses[data_obj.month - 1].capitalize()
    ano = data_obj.year

    return f"{dia} de {mes} de {ano}"


def duracao_texto(data_inicio, data_fim):
    dias = (data_fim - data_inicio).days

    if dias <= 1:
        return "1 dia"

    return f"{dias} dias"