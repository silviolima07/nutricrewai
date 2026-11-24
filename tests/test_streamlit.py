from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest


RAIZ = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8000/api/v1/analisar"


@pytest.mark.parametrize(("codigo", "resultado", "mensagem"), [
    (200, {"status": "analisado", "descricao": "Arroz", "relatorio": "Relatório"}, None),
    (200, {"status": "sem_alimentos", "descricao": "Prato vazio", "relatorio": None}, "Prato vazio"),
    (503, {"detail": "Serviço de análise ainda não configurado."}, "Serviço de análise ainda não configurado."),
])
def test_streamlit_envia_analise_e_exibe_resposta(monkeypatch, requests_mock, codigo, resultado, mensagem):
    dados = (RAIZ / "img" / "prato.png").read_bytes()
    arquivo = SimpleNamespace(
        name="prato.png", type="image/png", size=len(dados), getvalue=lambda: dados
    )
    monkeypatch.setenv("NUTRICREW_API_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr("streamlit.file_uploader", Mock(return_value=arquivo))
    rota = requests_mock.post(API, status_code=codigo, json=resultado)

    tela = AppTest.from_file(str(RAIZ / "app.py")).run()
    assert not tela.exception
    assert rota.call_count == 0
    tela.button[0].click().run()
    assert not tela.exception
    assert rota.call_count == 1
    envio = rota.last_request.body
    assert b'name="imagem"; filename="prato.png"' in envio
    assert b'name="observacoes"' in envio
    assert b"Manter o peso" in envio

    if codigo != 200:
        assert tela.error[0].value == mensagem
    elif mensagem:
        assert tela.info[0].value == mensagem
    else:
        assert tela.markdown[0].value == "Relatório"
        assert len(tela.get("download_button")) == 1
        tela.run()
        assert rota.call_count == 1
        assert len(tela.get("download_button")) == 1
