"""Publicação de posts de texto no perfil pessoal do LinkedIn (Posts API)."""

from __future__ import annotations

import datetime as dt
import os
import re

import requests

API_URL = "https://api.linkedin.com/rest/posts"

# Caracteres reservados do "Little Text Format" usado no campo `commentary`.
# Se não forem escapados, o LinkedIn corta o post no primeiro caractere reservado.
_RESERVADOS = set(r"\|{}@[]()<>#*_~")
_HASHTAG = re.compile(r"(?<![\w#])#(\w+)", re.UNICODE)


def versao_api() -> str:
    """Versão da API no formato AAAAMM.

    O LinkedIn desativa versões com cerca de 1 ano. Por padrão usamos a de
    3 meses atrás (sempre ativa); dá para fixar com LINKEDIN_VERSION.
    """
    fixa = os.environ.get("LINKEDIN_VERSION", "").strip()
    if fixa:
        return fixa
    hoje = dt.date.today()
    mes = hoje.month - 3
    ano = hoje.year
    if mes <= 0:
        mes += 12
        ano -= 1
    return f"{ano}{mes:02d}"


def _escapar(trecho: str) -> str:
    return "".join("\\" + c if c in _RESERVADOS else c for c in trecho)


def formatar_texto(texto: str) -> str:
    """Escapa caracteres reservados e transforma #hashtags em hashtags clicáveis."""
    partes = []
    ultimo = 0
    for m in _HASHTAG.finditer(texto):
        partes.append(_escapar(texto[ultimo : m.start()]))
        partes.append("{hashtag|\\#|" + _escapar(m.group(1)) + "}")
        ultimo = m.end()
    partes.append(_escapar(texto[ultimo:]))
    return "".join(partes)


def publicar(texto: str, token: str, autor_urn: str) -> str:
    """Publica o texto e devolve o link do post."""
    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": versao_api(),
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
        json={
            "author": autor_urn,
            "commentary": formatar_texto(texto),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        },
        timeout=30,
    )
    if resp.status_code == 401:
        raise RuntimeError(
            "Token do LinkedIn inválido ou expirado (dura 60 dias). "
            "Gere outro com scripts/obter_token.py e atualize o secret LINKEDIN_ACCESS_TOKEN."
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"LinkedIn respondeu {resp.status_code}: {resp.text[:500]}")
    urn = resp.headers.get("x-restli-id", "")
    return f"https://www.linkedin.com/feed/update/{urn}/" if urn else "(publicado, sem URN)"
