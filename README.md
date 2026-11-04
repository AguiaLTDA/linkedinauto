# Posts automáticos no LinkedIn com o Claude

Você escreve as pautas numa planilha. O Claude redige os posts e você aprova. A publicação no seu perfil é automática.

```
pendente ──(Claude gera rascunho)──▶ revisar ──(você aprova)──▶ aprovado ──(no dia)──▶ publicado
```

Todo dia às 08:17 (horário de Brasília), o GitHub Actions faz duas coisas:
1. **Gerar:** para as linhas `pendente` com data nos próximos 3 dias, o Claude escreve o texto, preenche a coluna `texto` e muda o status para `revisar`.
2. **Publicar:** para as linhas `aprovado` cuja data já chegou, publica no LinkedIn e preenche `link`. São no máximo 1 post por dia.

**Nada é publicado sem que você mude o status para `aprovado`.** Você pode editar o texto à vontade antes de aprovar.

---

## Configuração (uma vez só, cerca de 30 min)

### 1. Planilha no Google Sheets
1. Crie uma planilha nova e importe o arquivo `planilha_modelo.csv` (Arquivo → Importar).
2. Confira se a primeira linha tem exatamente estas colunas: `data, tema, instrucoes, status, texto, link, observacao`.
3. Copie o **ID da planilha**, que é o trecho da URL entre `/d/` e `/edit`.
4. Dica: em `status`, use Dados → Validação de dados → lista com `pendente, revisar, aprovado, publicado, erro`.

### 2. Conta de serviço do Google (para o robô ler e escrever na planilha)
1. Em https://console.cloud.google.com, crie um projeto e ative a **Google Sheets API**.
2. Vá em IAM → Contas de serviço → Criar. Depois, em Chaves → Adicionar chave → JSON, baixe o arquivo.
3. Compartilhe a planilha (botão Compartilhar) com o e-mail da conta de serviço (`...@...iam.gserviceaccount.com`) como **Editor**.

### 3. App no LinkedIn
1. Em https://www.linkedin.com/developers/apps, crie um app. Ele exige associar uma Página de empresa; pode ser uma página da instituição ou uma página sua.
2. Na aba **Products**, adicione **Share on LinkedIn** e **Sign In with LinkedIn using OpenID Connect**.
3. Na aba **Auth**, em *Authorized redirect URLs*, adicione `http://localhost:8765/callback`.
4. Anote o **Client ID** e o **Client Secret**.
5. No seu computador, rode:
   ```bash
   pip install requests
   ```
   ```bash
   LINKEDIN_CLIENT_ID=seu_id LINKEDIN_CLIENT_SECRET=seu_secret python scripts/obter_token.py
   ```
   O navegador abre, você autoriza, e o script imprime `LINKEDIN_ACCESS_TOKEN` e `LINKEDIN_PERSON_URN`.

> ⚠️ **O token do LinkedIn vale 60 dias.** Marque um lembrete para rodar o `obter_token.py` de novo e atualizar o secret. Quando o token vencer, a linha fica com status `erro` e uma explicação na coluna `observacao`.

### 4. Chave da API do Claude
Crie em https://platform.claude.com, em Settings → API Keys.

### 5. Repositório no GitHub
1. Crie um repositório **privado** e envie esta pasta para ele.
2. Em Settings → Secrets and variables → Actions → **Secrets**, crie:

| Secret | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | chave do Claude |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | conteúdo inteiro do JSON baixado no passo 2 |
| `PLANILHA_ID` | ID da planilha |
| `LINKEDIN_ACCESS_TOKEN` | impresso pelo `obter_token.py` |
| `LINKEDIN_PERSON_URN` | impresso pelo `obter_token.py` (`urn:li:person:...`) |

3. Opcional, em **Variables**: `PLANILHA_ABA` (nome da aba, se não for a primeira), `DIAS_ANTECEDENCIA` (padrão 3) e `MAX_POSTS_POR_EXECUCAO` (padrão 1).

### 6. Personalize a voz
Edite `config/estilo.md` com seu nome, cargo, tom e formato preferidos. O Claude segue esse guia em todos os posts.

### 7. Teste
Em Actions → **Posts no LinkedIn** → *Run workflow*, marque **Só simular**. O log mostra os rascunhos e o que seria publicado, sem gravar nada. Depois rode sem simular.

---

## Dia a dia
- **Nova pauta:** adicione uma linha com `data` (dd/mm/aaaa), `tema`, `instrucoes` (opcional) e status `pendente`.
- **Revisar:** quando o status virar `revisar`, leia e edite a coluna `texto`. Se estiver bom, mude para `aprovado`.
- **Refazer um rascunho:** apague o `texto` e volte o status para `pendente`.
- **Publicar na hora:** coloque a data de hoje, aprove e rode o workflow manualmente com a ação `publicar`.

## Rodar localmente (opcional)
```bash
pip install -r requirements.txt
```
```bash
python src/main.py tudo --simular
```
(Exporte as mesmas variáveis dos secrets antes.) Testes: `python -m pytest tests`.

## Custos
- Claude (modelo `claude-opus-5-5`): alguns centavos de dólar por post.
- GitHub Actions: gratuito para esse uso, mesmo em repositório privado.
- LinkedIn e Google Sheets: gratuitos.
