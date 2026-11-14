
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VisionResult:
    descricao: str
    provedor: str


class VisionProvider(Protocol):

    def descrever(
        self,
        imagem: bytes,
        mime_type: str,
        prompt: str
    ) -> VisionResult:
        ...
