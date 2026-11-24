from io import BytesIO
from unittest.mock import Mock

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app.api import ConfiguracaoIncompleta, MAX_BYTES, criar_api
from app.workflows.meal_analysis import RespostaVisaoInvalida


URL = "/api/v1/analisar"


def imagem_png():
    arquivo = BytesIO()
    Image.new("RGB", (4, 4)).save(arquivo, format="PNG")
    return arquivo.getvalue()


@pytest.mark.parametrize("resultado", [
    {"status": "analisado", "descricao": "Arroz", "relatorio": "Relatório"},
    {"status": "sem_alimentos", "descricao": "Prato vazio", "relatorio": None},
])
def test_api_encaminha_imagem_e_observacoes(resultado):
    executor = Mock(return_value=resultado)
    client = TestClient(criar_api(lambda: executor))
    dados = imagem_png()

    resposta = client.post(URL, files=[
        ("imagem", ("prato.png", dados, "image/png")),
        ("observacoes", (None, " Manter o peso ")),
        ("observacoes", (None, "Sem amendoim")),
    ])

    assert resposta.status_code == 200
    assert resposta.json() == resultado
    executor.assert_called_once_with({
        "imagem": dados,
        "mime_type": "image/png",
        "observacoes": ["Manter o peso", "Sem amendoim"],
    })


@pytest.mark.parametrize(("conteudo", "mime_type", "status"), [
    (b"", "image/png", 422),
    (b"arquivo invalido", "image/png", 422),
    (imagem_png(), "image/jpeg", 415),
    (imagem_png(), "image/gif", 415),
    (b"x" * (MAX_BYTES + 1), "image/png", 413),
])
def test_api_rejeita_arquivo_invalido(conteudo, mime_type, status):
    obter_executor = Mock()
    client = TestClient(criar_api(obter_executor))

    resposta = client.post(URL, files={"imagem": ("arquivo", conteudo, mime_type)})

    assert resposta.status_code == status
    obter_executor.assert_not_called()


def test_api_nao_expoe_detalhes_da_falha_do_provedor():
    executor = Mock(side_effect=RespostaVisaoInvalida("detalhe interno"))
    client = TestClient(criar_api(lambda: executor))

    resposta = client.post(URL, files={"imagem": ("prato.png", imagem_png(), "image/png")})

    assert resposta.status_code == 502
    assert resposta.json() == {"detail": "Não foi possível concluir a análise."}
    assert executor.call_args.args[0]["observacoes"] == []


def test_api_informa_configuracao_incompleta():
    obter_executor = Mock(side_effect=ConfiguracaoIncompleta)
    client = TestClient(criar_api(obter_executor))

    resposta = client.post(URL, files={"imagem": ("prato.png", imagem_png(), "image/png")})

    assert resposta.status_code == 503
