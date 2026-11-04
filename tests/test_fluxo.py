import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import main  # noqa: E402
from linkedin import formatar_texto  # noqa: E402
from planilha import Planilha  # noqa: E402


class AbaFalsa:
    def __init__(self, linhas):
        self.linhas = [list(l) for l in linhas]

    def row_values(self, n):
        return self.linhas[n - 1]

    def get_all_values(self):
        return [list(l) for l in self.linhas]

    def update_cell(self, linha, col, valor):
        self.linhas[linha - 1][col - 1] = valor


CAB = ["data", "tema", "instrucoes", "status", "texto", "link", "observacao"]


def fmt(d):
    return d.strftime("%d/%m/%Y")


def test_formatar_texto_escapa_e_cria_hashtags():
    saida = formatar_texto("Olá (turma) @todos! #Educacao #univc")
    assert saida == r"Olá \(turma\) \@todos! {hashtag|\#|Educacao} {hashtag|\#|univc}"


def test_fluxo_completo(monkeypatch):
    hoje = main.hoje()
    aba = AbaFalsa([
        CAB,
        [fmt(hoje), "Tema A", "", "pendente", "", "", ""],
        [fmt(hoje + dt.timedelta(days=30)), "Tema longe", "", "pendente", "", "", ""],
        ["32/13/2026", "Data ruim", "", "", "", "", ""],
        [fmt(hoje), "Tema B", "", "aprovado", "Texto pronto", "", ""],
        [fmt(hoje + dt.timedelta(days=1)), "Amanhã", "", "aprovado", "Ainda não", "", ""],
    ])
    p = Planilha(aba)

    assert main.gerar(p, False, lambda t, i, d: f"post sobre {t}") == 1
    assert aba.linhas[1][3] == "revisar" and aba.linhas[1][4] == "post sobre Tema A"
    assert aba.linhas[2][3] == "pendente"  # data distante não é gerada
    assert "Data inválida" in aba.linhas[3][6]

    publicados = []
    assert main.publicar(p, False, lambda t: publicados.append(t) or "https://x/1") == 1
    assert publicados == ["Texto pronto"]
    assert aba.linhas[4][3] == "publicado" and aba.linhas[4][5] == "https://x/1"
    assert aba.linhas[5][3] == "aprovado"  # data futura espera
    # rascunho em "revisar" nunca é publicado sem aprovação
    assert aba.linhas[1][3] == "revisar"


def test_simular_nao_altera_planilha():
    hoje = main.hoje()
    aba = AbaFalsa([CAB, [fmt(hoje), "Tema", "", "aprovado", "Texto", "", ""]])
    antes = aba.get_all_values()
    main.publicar(Planilha(aba), True, lambda t: (_ for _ in ()).throw(AssertionError("não deveria publicar")))
    assert aba.get_all_values() == antes
