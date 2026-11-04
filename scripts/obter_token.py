"""Obtém o token de acesso do LinkedIn e o URN do seu perfil.

Rode no SEU computador (abre o navegador para você autorizar o app):

    LINKEDIN_CLIENT_ID=... LINKEDIN_CLIENT_SECRET=... python scripts/obter_token.py

No app do LinkedIn Developers, cadastre esta URL de redirecionamento:
    http://localhost:8765/callback

Ao final, copie os dois valores impressos para os secrets do GitHub:
    LINKEDIN_ACCESS_TOKEN  e  LINKEDIN_PERSON_URN
O token vale 60 dias; repita este script antes de vencer.
"""

from __future__ import annotations

import http.server
import os
import secrets
import urllib.parse
import webbrowser

import requests

PORTA = 8765
REDIRECT = f"http://localhost:{PORTA}/callback"
ESCOPOS = "openid profile w_member_social"


def main() -> None:
    client_id = os.environ["LINKEDIN_CLIENT_ID"]
    client_secret = os.environ["LINKEDIN_CLIENT_SECRET"]
    estado = secrets.token_urlsafe(16)
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(
        {"response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT, "scope": ESCOPOS, "state": estado}
    )

    recebido: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            recebido.update({k: v[0] for k, v in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Pronto! Pode fechar esta aba e voltar ao terminal.</h2>".encode())

        def log_message(self, *args):
            pass

    print("Abrindo o navegador para autorizar o app no LinkedIn...\nSe não abrir, acesse:\n" + url)
    webbrowser.open(url)
    with http.server.HTTPServer(("localhost", PORTA), Handler) as servidor:
        servidor.handle_request()

    if recebido.get("state") != estado:
        raise SystemExit("Resposta inválida (state não confere). Tente de novo.")
    if "code" not in recebido:
        raise SystemExit(f"Autorização negada: {recebido}")

    token = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": recebido["code"],
            "redirect_uri": REDIRECT,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    token.raise_for_status()
    dados = token.json()
    acesso = dados["access_token"]

    perfil = requests.get(
        "https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {acesso}"}, timeout=30
    )
    perfil.raise_for_status()
    info = perfil.json()

    dias = int(dados.get("expires_in", 0)) // 86400
    print(f"\nConectado como: {info.get('name')}")
    print(f"Validade do token: {dias} dias\n")
    print(f"LINKEDIN_ACCESS_TOKEN = {acesso}")
    print(f"LINKEDIN_PERSON_URN   = urn:li:person:{info['sub']}")


if __name__ == "__main__":
    main()
