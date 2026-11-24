import json
from typing import Literal, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.nutrition_service import NutritionService
from app.services.vision_service import VisionService


PROMPT_VISAO = """
Identifique apenas alimentos visíveis e reconhecíveis na imagem.
Responda em português com um objeto JSON, sem explicações ou Markdown:
{"tem_alimentos": true, "descricao": "descrição dos alimentos identificados"}
Se não houver alimentos identificáveis, use:
{"tem_alimentos": false, "descricao": ""}
"""


class RespostaVisaoInvalida(ValueError):
    """O provedor respondeu fora do formato esperado para a análise."""


class EntradaAnalise(TypedDict):
    imagem: bytes
    mime_type: str
    observacoes: list[str]


class ResultadoAnalise(TypedDict):
    status: Literal["analisado", "sem_alimentos"]
    descricao: str
    relatorio: str | None


class EstadoAnalise(EntradaAnalise):
    descricao: NotRequired[str]
    tem_alimentos: NotRequired[bool]
    status: NotRequired[Literal["analisado", "sem_alimentos"]]
    relatorio: NotRequired[str | None]


def criar_fluxo_analise(visao: VisionService, nutricao: NutritionService):
    def descrever_imagem(estado: EstadoAnalise):
        resposta = visao.descrever(
            estado["imagem"], estado["mime_type"], PROMPT_VISAO
        )
        texto = resposta.descricao.strip()
        if texto.startswith("```") and texto.endswith("```"):
            texto = texto.partition("\n")[2].removesuffix("```").strip()

        try:
            dados = json.loads(texto)
        except ValueError:
            raise RespostaVisaoInvalida("Resposta de visão inválida.") from None

        if (
            not isinstance(dados, dict)
            or not isinstance(dados.get("tem_alimentos"), bool)
            or not isinstance(dados.get("descricao"), str)
            or (dados["tem_alimentos"] and not dados["descricao"].strip())
        ):
            raise RespostaVisaoInvalida("Resposta de visão inválida.")

        return {
            "tem_alimentos": dados["tem_alimentos"],
            "descricao": dados["descricao"].strip(),
        }

    def escolher_rota(estado: EstadoAnalise) -> Literal[
        "analisar_nutricao", "sem_alimentos"
    ]:
        return "analisar_nutricao" if estado["tem_alimentos"] else "sem_alimentos"

    def analisar_nutricao(estado: EstadoAnalise):
        relatorio = nutricao.analisar(
            estado["descricao"], list(estado["observacoes"])
        )
        return {"status": "analisado", "relatorio": relatorio}

    def sem_alimentos(estado: EstadoAnalise):
        return {
            "status": "sem_alimentos",
            "descricao": "Nenhum alimento identificável foi encontrado na imagem.",
            "relatorio": None,
        }

    grafo = StateGraph(
        EstadoAnalise, input_schema=EntradaAnalise, output_schema=ResultadoAnalise
    )
    grafo.add_node("descrever_imagem", descrever_imagem)
    grafo.add_node("analisar_nutricao", analisar_nutricao)
    grafo.add_node("sem_alimentos", sem_alimentos)
    grafo.add_edge(START, "descrever_imagem")
    grafo.add_conditional_edges("descrever_imagem", escolher_rota)
    grafo.add_edge("analisar_nutricao", END)
    grafo.add_edge("sem_alimentos", END)
    return grafo.compile()
