from unittest.mock import Mock

import pytest

from app.services.nutrition_service import NutritionService
from app.services.vision_provider import VisionResult
from app.services.vision_service import VisionService
from app.workflows.meal_analysis import RespostaVisaoInvalida, criar_fluxo_analise


def preparar_fluxo(resposta: str):
    visao = Mock(spec=VisionService)
    visao.descrever.return_value = VisionResult(resposta, "groq")
    nutricao = Mock(spec=NutritionService)
    nutricao.analisar.return_value = "Relatório nutricional"
    return criar_fluxo_analise(visao, nutricao), nutricao


ENTRADA = {
    "imagem": b"imagem",
    "mime_type": "image/png",
    "observacoes": ["Manter o peso"],
}


def test_analisa_imagem_com_alimentos():
    fluxo, nutricao = preparar_fluxo(
        '{"tem_alimentos": true, "descricao": "Arroz e feijão"}'
    )

    assert fluxo.invoke(ENTRADA) == {
        "status": "analisado",
        "descricao": "Arroz e feijão",
        "relatorio": "Relatório nutricional",
    }
    nutricao.analisar.assert_called_once_with("Arroz e feijão", ["Manter o peso"])


def test_encerra_analise_quando_nao_ha_alimentos():
    fluxo, nutricao = preparar_fluxo(
        '{"tem_alimentos": false, "descricao": ""}'
    )

    assert fluxo.invoke(ENTRADA) == {
        "status": "sem_alimentos",
        "descricao": "Nenhum alimento identificável foi encontrado na imagem.",
        "relatorio": None,
    }
    nutricao.analisar.assert_not_called()


@pytest.mark.parametrize("resposta", [
    "Não tenho certeza",
    '{"tem_alimentos": "false", "descricao": ""}',
    '{"tem_alimentos": true, "descricao": " "}',
])
def test_resposta_invalida_nao_dispara_analise_nutricional(resposta):
    fluxo, nutricao = preparar_fluxo(resposta)

    with pytest.raises(RespostaVisaoInvalida, match="Resposta de visão inválida"):
        fluxo.invoke(ENTRADA)

    nutricao.analisar.assert_not_called()
