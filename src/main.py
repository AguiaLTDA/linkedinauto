"""Automação de posts no LinkedIn com o Claude e aprovação humana.

Fluxo (cada linha da planilha é um post):
  pendente  --(gerar)-->  revisar  --(você muda para)-->  aprovado  --(publicar)-->  publicado

Uso:
  python src/main.py gerar      # cria rascunhos para os posts dos próximos dias
  python src/main.py publicar   # publica os posts aprovados cuja data já chegou
  python src/main.py tudo       # os dois, nessa ordem
Adicione --simular para ver o que aconteceria sem gravar nada nem publicar.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

FUSO = ZoneInfo(os.environ.get("FUSO_HORARIO", "America/Sao_Paulo"))


def hoje() -> dt.date:
    return dt.datetime.now(FUSO).date()


def ler_data(texto: str) -> dt.date | None:
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            continue
    return None


def agora_txt() -> str:
    return dt.datetime.now(FUSO).strftime("%d/%m/%Y %H:%M")


def gerar(planilha, simular: bool, gerar_post) -> int:
    antecedencia = int(os.environ.get("DIAS_ANTECEDENCIA", "3"))
    limite = hoje() + dt.timedelta(days=antecedencia)
    feitos = 0
    for n, reg in planilha.linhas():
        if reg["status"].lower() not in ("", "pendente"):
            continue
        data = ler_data(reg["data"])
        if data is None:
            print(f"Linha {n}: data inválida '{reg['data']}' (use dd/mm/aaaa).")
            if not simular:
                planilha.atualizar(n, observacao="Data inválida: use dd/mm/aaaa")
            continue
        if data > limite:
            continue
        print(f"Linha {n}: gerando rascunho sobre '{reg['tema']}'...")
        try:
            texto = gerar_post(reg["tema"], reg["instrucoes"], reg["data"])
        except Exception as erro:  # registra e segue para as próximas linhas
            print(f"  erro: {erro}")
            if not simular:
                planilha.atualizar(n, observacao=f"Erro ao gerar: {erro}"[:500])
            continue
        if simular:
            print("-" * 60 + f"\n{texto}\n" + "-" * 60)
        else:
            planilha.atualizar(n, texto=texto, status="revisar", observacao=f"Rascunho gerado em {agora_txt()}")
        feitos += 1
    print(f"Rascunhos gerados: {feitos}")
    return feitos


def publicar(planilha, simular: bool, publicar_post) -> int:
    maximo = int(os.environ.get("MAX_POSTS_POR_EXECUCAO", "1"))
    feitos = 0
    for n, reg in planilha.linhas():
        if feitos >= maximo:
            break
        if reg["status"].lower() != "aprovado":
            continue
        data = ler_data(reg["data"])
        if data is None or data > hoje():
            continue
        if not reg["texto"]:
            if not simular:
                planilha.atualizar(n, observacao="Aprovado, mas a coluna texto está vazia")
            continue
        print(f"Linha {n}: publicando no LinkedIn...")
        if simular:
            print(f"  (simulação) publicaria {len(reg['texto'])} caracteres")
            feitos += 1
            continue
        try:
            link = publicar_post(reg["texto"])
        except Exception as erro:
            print(f"  erro: {erro}")
            planilha.atualizar(n, status="erro", observacao=f"Erro ao publicar: {erro}"[:500])
            continue
        planilha.atualizar(n, status="publicado", link=link, observacao=f"Publicado em {agora_txt()}")
        print(f"  publicado: {link}")
        feitos += 1
    print(f"Posts publicados: {feitos}")
    return feitos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("acao", choices=["gerar", "publicar", "tudo"])
    parser.add_argument("--simular", action="store_true", help="não grava na planilha nem publica")
    args = parser.parse_args()

    from planilha import Planilha

    planilha = Planilha.conectar()

    if args.acao in ("gerar", "tudo"):
        from redator import gerar_post

        gerar(planilha, args.simular, gerar_post)

    if args.acao in ("publicar", "tudo"):
        from linkedin import publicar as publicar_linkedin

        token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        autor = os.environ.get("LINKEDIN_PERSON_URN", "")
        if not args.simular and not (token and autor):
            print("Faltam LINKEDIN_ACCESS_TOKEN e/ou LINKEDIN_PERSON_URN.", file=sys.stderr)
            return 1
        publicar(planilha, args.simular, lambda texto: publicar_linkedin(texto, token, autor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
