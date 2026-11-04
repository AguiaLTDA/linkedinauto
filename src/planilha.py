"""Acesso ao calendário editorial no Google Sheets."""

from __future__ import annotations

import json
import os

COLUNAS = ["data", "tema", "instrucoes", "status", "texto", "link", "observacao"]


class Planilha:
    def __init__(self, aba) -> None:
        self.aba = aba
        cabecalho = [c.strip().lower() for c in aba.row_values(1)]
        faltando = [c for c in COLUNAS if c not in cabecalho]
        if faltando:
            raise RuntimeError(f"Colunas ausentes na planilha: {', '.join(faltando)}")
        self.col = {nome: cabecalho.index(nome) + 1 for nome in COLUNAS}

    @classmethod
    def conectar(cls) -> "Planilha":
        import gspread

        credenciais = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
        gc = gspread.service_account_from_dict(credenciais)
        planilha = gc.open_by_key(os.environ["PLANILHA_ID"])
        nome_aba = os.environ.get("PLANILHA_ABA", "").strip()
        return cls(planilha.worksheet(nome_aba) if nome_aba else planilha.sheet1)

    def linhas(self):
        """Gera (numero_da_linha, dict) para cada linha preenchida."""
        valores = self.aba.get_all_values()
        for i, linha in enumerate(valores[1:], start=2):
            linha = linha + [""] * (len(valores[0]) - len(linha))
            registro = {nome: linha[idx - 1].strip() for nome, idx in self.col.items()}
            if registro["tema"]:
                yield i, registro

    def atualizar(self, linha: int, **campos: str) -> None:
        for nome, valor in campos.items():
            self.aba.update_cell(linha, self.col[nome], valor)
