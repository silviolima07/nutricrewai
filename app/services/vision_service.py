
from .vision_provider import VisionProvider, VisionResult


class RecoverableVisionError(Exception):
    """Falha que permite tentar outro provedor."""
    pass


class VisionService:
    def __init__(
        self,
        principal: VisionProvider,
        secundario: VisionProvider
    ):
        self.principal = principal
        self.secundario = secundario

    def descrever(
        self,
        imagem: bytes,
        mime_type: str,
        prompt: str
    ) -> VisionResult:

        try:
            return self.principal.descrever(
                imagem, mime_type, prompt
            )

        except RecoverableVisionError:
            return self.secundario.descrever(
                imagem, mime_type, prompt
            )
