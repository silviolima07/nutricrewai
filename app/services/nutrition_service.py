
from typing import Callable


class NutritionService:

    def __init__(self, crew_factory: Callable):
        self.crew_factory = crew_factory

    def analisar(
        self,
        descricao: str,
        observacoes: list[str]
    ) -> str:

        if not descricao.strip():
            raise ValueError("Descricao vazia")

        inputs = {
            "descricao": descricao,
            "observacoes": observacoes
        }

        crew = self.crew_factory()

        return crew.kickoff(inputs=inputs)