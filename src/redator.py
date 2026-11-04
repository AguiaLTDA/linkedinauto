"""Geração do texto do post com o Claude."""

from __future__ import annotations

from pathlib import Path

import anthropic

MODELO = "claude-opus-5-5"
ESTILO_PADRAO = Path(__file__).resolve().parent.parent / "config" / "estilo.md"

INSTRUCOES = """Você escreve posts para o perfil pessoal de LinkedIn de uma pessoa.
Siga o guia de estilo abaixo à risca. Responda APENAS com o texto final do post,
pronto para publicar: sem título, sem aspas, sem comentários sobre o texto e sem
marcação Markdown (LinkedIn não renderiza **negrito** nem # títulos).

<guia_de_estilo>
{estilo}
</guia_de_estilo>"""


def gerar_post(tema: str, instrucoes: str = "", data: str = "", estilo_path: Path = ESTILO_PADRAO) -> str:
    estilo = estilo_path.read_text(encoding="utf-8")
    pedido = f"Tema do post: {tema.strip()}"
    if instrucoes.strip():
        pedido += f"\nOrientações específicas: {instrucoes.strip()}"
    if data.strip():
        pedido += f"\nData prevista de publicação: {data.strip()}"

    client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
    resposta = client.beta.messages.create(
        model=MODELO,
        max_tokens=16000,
        output_config={"effort": "medium"},
        # Se o modelo recusar por política, o próprio servidor tenta outro modelo.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=INSTRUCOES.format(estilo=estilo),
        messages=[{"role": "user", "content": pedido}],
    )
    if resposta.stop_reason == "refusal":
        raise RuntimeError("O Claude recusou gerar este post; reveja o tema.")
    texto = "".join(b.text for b in resposta.content if b.type == "text").strip()
    if not texto:
        raise RuntimeError(f"Resposta vazia do Claude (stop_reason={resposta.stop_reason}).")
    if len(texto) > 3000:
        raise RuntimeError(f"Post com {len(texto)} caracteres; o limite do LinkedIn é 3000.")
    return texto
