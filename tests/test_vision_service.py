
import pytest

from app.services.vision_provider import VisionResult
from app.services.vision_service import (
    VisionService,
    RecoverableVisionError,
)


class ProvedorSimulado:
    def __init__(self, nome, falhar=False):
        self.nome = nome
        self.falhar = falhar
        self.chamadas = 0

    def descrever(self, imagem, mime_type, prompt):
        self.chamadas += 1

        if self.falhar:
            raise RecoverableVisionError(
                f"{self.nome} indisponível"
            )

        return VisionResult(
            descricao="Arroz, feijão e frango",
            provedor=self.nome,
        )


def test_groq_funciona():
    groq = ProvedorSimulado("groq")
    openrouter = ProvedorSimulado("openrouter")

    servico = VisionService(groq, openrouter)
    resultado = servico.descrever(
        b"imagem", "image/jpeg", "Descreva"
    )

    assert resultado.provedor == "groq"
    assert groq.chamadas == 1
    assert openrouter.chamadas == 0


def test_fallback_openrouter():
    groq = ProvedorSimulado("groq", falhar=True)
    openrouter = ProvedorSimulado("openrouter")

    servico = VisionService(groq, openrouter)
    resultado = servico.descrever(
        b"imagem", "image/jpeg", "Descreva"
    )

    assert resultado.provedor == "openrouter"
    assert groq.chamadas == 1
    assert openrouter.chamadas == 1


def test_ambos_falham():
    groq = ProvedorSimulado("groq", falhar=True)
    openrouter = ProvedorSimulado(
        "openrouter", falhar=True
    )

    servico = VisionService(groq, openrouter)

    with pytest.raises(RecoverableVisionError):
        servico.descrever(
            b"imagem", "image/jpeg", "Descreva"
        )

    assert groq.chamadas == 1
    assert openrouter.chamadas == 1
