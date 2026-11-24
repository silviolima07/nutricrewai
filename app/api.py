from collections.abc import Callable
from functools import lru_cache, partial
from io import BytesIO
import logging
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.config import Settings
from app.services.nutrition_service import NutritionService
from app.services.providers.groq_provider import GroqProvider
from app.services.providers.openrouter_provider import OpenRouterProvider
from app.services.vision_service import VisionService
from app.workflows.meal_analysis import (
    EntradaAnalise,
    ResultadoAnalise,
    criar_fluxo_analise,
)


MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000
FORMATOS = {"JPEG": "image/jpeg", "PNG": "image/png"}
logger = logging.getLogger(__name__)


class ConfiguracaoIncompleta(RuntimeError):
    """Faltam credenciais ou modelos para executar a análise."""


class RespostaAnalise(BaseModel):
    status: Literal["analisado", "sem_alimentos"]
    descricao: str
    relatorio: str | None


@lru_cache(maxsize=1)
def obter_analisador() -> Callable[[EntradaAnalise], ResultadoAnalise]:
    settings = Settings()
    modelo_nutricional = settings.groq_nutrition_model or settings.groq_vision_model
    if not all((
        settings.groq_api_key,
        settings.groq_vision_model,
        settings.openrouter_api_key,
        settings.openrouter_vision_model,
        modelo_nutricional,
    )):
        raise ConfiguracaoIncompleta

    from app.services.crew_nutri import CrewNutri

    visao = VisionService(
        GroqProvider(settings.groq_api_key, settings.groq_vision_model),
        OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_vision_model),
    )
    nutricao = NutritionService(partial(CrewNutri, model=modelo_nutricional))
    return criar_fluxo_analise(visao, nutricao).invoke


def validar_imagem(arquivo: UploadFile) -> tuple[bytes, str]:
    dados = arquivo.file.read(MAX_BYTES + 1)
    if len(dados) > MAX_BYTES:
        raise HTTPException(413, "A imagem deve ter no máximo 5 MiB.")
    if not dados:
        raise HTTPException(422, "O arquivo de imagem está vazio.")
    if arquivo.content_type not in FORMATOS.values():
        raise HTTPException(415, "Envie uma imagem JPEG ou PNG.")

    try:
        with Image.open(BytesIO(dados), formats=list(FORMATOS)) as imagem:
            mime_type = FORMATOS[imagem.format]
            if mime_type != arquivo.content_type:
                raise HTTPException(415, "O conteúdo da imagem diverge do tipo informado.")
            if imagem.width * imagem.height > MAX_PIXELS:
                raise HTTPException(413, "A imagem deve ter no máximo 25 megapixels.")
            imagem.verify()
        with Image.open(BytesIO(dados), formats=list(FORMATOS)) as imagem:
            imagem.load()
    except Image.DecompressionBombError:
        raise HTTPException(413, "A imagem deve ter no máximo 25 megapixels.") from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise HTTPException(422, "Não foi possível ler a imagem enviada.") from None
    return dados, mime_type


def criar_api(
    obter_executor: Callable[[], Callable[[EntradaAnalise], ResultadoAnalise]] = obter_analisador,
) -> FastAPI:
    api = FastAPI(title="NutriCrewAI", version="1.0.0")

    @api.post("/api/v1/analisar", response_model=RespostaAnalise)
    def analisar(
        imagem: Annotated[UploadFile, File()],
        observacoes: Annotated[list[str] | None, Form()] = None,
    ):
        dados, mime_type = validar_imagem(imagem)
        entrada: EntradaAnalise = {
            "imagem": dados,
            "mime_type": mime_type,
            "observacoes": [texto.strip() for texto in observacoes or [] if texto.strip()],
        }

        try:
            executor = obter_executor()
        except ConfiguracaoIncompleta:
            raise HTTPException(503, "Serviço de análise ainda não configurado.") from None

        try:
            return executor(entrada)
        except Exception as erro:
            logger.warning("Falha na análise (%s).", type(erro).__name__)
            raise HTTPException(502, "Não foi possível concluir a análise.") from None

    return api


app = criar_api()
