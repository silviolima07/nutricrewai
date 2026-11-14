
import pytest

from app.services.nutrition_service import NutritionService


class CrewSimulada:
    def kickoff(self, inputs):
        return (
            f"Alimentos: {inputs['descricao']}; "
            f"Observacoes: {inputs['observacoes']}"
        )


def test_analise_nutricional():
    servico = NutritionService(CrewSimulada)

    resultado = servico.analisar(
        descricao="Arroz e feijao",
        observacoes=["Manter o peso"]
    )

    assert "Arroz e feijao" in resultado
    assert "Manter o peso" in resultado


def test_descricao_vazia():
    servico = NutritionService(CrewSimulada)

    with pytest.raises(ValueError, match="Descricao vazia"):
        servico.analisar(
            descricao="   ",
            observacoes=[]
        )
