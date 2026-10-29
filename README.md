# Central de Rotas — Demonstração visual 0.4

## Atualização visual 0.5

A interface ganhou balões de conversa semelhantes aos de mensageiros, indicadores de status com cores, cartões com origem/destino/data/horário e identificação do motorista responsável. Os botões de aceitar, iniciar e concluir continuam chamando os comandos originais do bot, sem substituir as regras de atribuição.

**Validação recomendada após o deploy:** entrar como Cliente, cadastrar uma rota fictícia, aceitar como Motorista A, conferir que ela saiu da lista disponível para Motorista B e consultar o motorista responsável como Administrador.

Essa aplicação é apenas uma demonstração no navegador. Não recebe mensagens reais do WhatsApp, não possui autenticação efetiva e utiliza banco SQLite temporário por sessão. Não utilize dados reais ou informações sensíveis.


Demo web em Streamlit usando a **lógica verdadeira de `bot.py` da versão 0.3**. A interação parece um WhatsApp, mas **não envia nem recebe mensagens pelo WhatsApp de verdade**.

## Rodar no computador (Windows + VS Code)

1. Abra esta pasta no VS Code.
2. No Terminal/PowerShell, execute:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run streamlit_app.py
```

3. Abra o endereço mostrado pelo Streamlit (normalmente http://localhost:8501).
4. Se o comando `py` não funcionar, experimente `python`.

## Publicar gratuitamente pelo Streamlit Community Cloud

1. Crie ou entre na sua conta em https://github.com e crie um repositório (ex.: `central-de-rotas-demo`). Pode ser **público**, desde que use apenas arquivos desta demo e nenhum dado pessoal, segredo ou banco real.
2. Abra o repositório e clique em **Add file > Upload files**. **Extraia o ZIP antes** e envie os arquivos da pasta: `streamlit_app.py`, `bot.py`, `banco.py`, `mensagens.py`, `demo_data.py`, `requirements.txt`, `README.md` e, opcionalmente, a pasta `.streamlit`. O `streamlit_app.py` deve ficar na raiz do repositório, não dentro de uma pasta extra. Finalize em **Commit changes**.
3. Acesse https://share.streamlit.io e entre com GitHub.
4. Clique **Create app** (ou **New app**) e escolha o repositório. Selecione a branch `main` e o arquivo principal `streamlit_app.py`.
5. Clique **Deploy**. Quando a publicação terminar, copie o link `https://...streamlit.app` em **Share** para mostrar à empresa.

Se preferir repositório privado, configure as permissões de compartilhamento do app no Streamlit. Verifique as regras atuais de acesso gratuito ao usar apps privados.

## Roteiro de apresentação

1. Em **Cliente**, selecione **Nova rota**, responda às perguntas e confirme com `S`.
2. Mude para **Motorista A** e clique em **Aceitar esta rota**. O comando `/aceitar ID` é executado pelo `bot.py`.
3. Mude para **Motorista B**. A rota aceita desapareceu da lista de disponíveis. Se digitar `/aceitar ID`, o bot recusa a tentativa.
4. Mude para **Administrador** para ver a situação e, se necessário, liberar uma rota atribuída.
5. Clique em **Reiniciar demonstração** para limpar todos os registros da sessão.

## O que deve ser entendido antes de compartilhar

- **Ambiente de apresentação, não serviço de operação real.** Os perfis são fictícios e a troca de perfil é livre; não há autenticação real.
- **Cada sessão de navegador possui banco SQLite separado**, no armazenamento temporário do servidor. Duas pessoas abrindo o link não compartilham as mesmas rotas; isso é intencional para evitar interferência entre demonstrações.
- Os dados podem desaparecer ao reiniciar/suspender o aplicativo, expirar o servidor ou reiniciar a demonstração.
- Não coloque telefones reais, dados de clientes, endereços precisos de pessoas nem informações confidenciais neste ambiente.
- A lógica real da produção exigirá webhook oficial do WhatsApp, autenticação, banco persistente, logs e backups, controles de acesso, LGPD e hospedagem adequada.

## Arquivos

- `streamlit_app.py`: interface gráfica de demonstração
- `demo_data.py`: cria cenário fictício com dois motoristas e rotas de exemplo
- `bot.py`: cadastro, comandos, validação e regras de atribuição reutilizados da v0.3
- `banco.py`: SQLite, com caminho isolado por sessão usando `ContextVar`
- `mensagens.py`: ligação entre interface e bot
- `requirements.txt`: biblioteca Streamlit

## Testes locais

Para verificar apenas a lógica de negócio:

```powershell
py -m unittest discover -s tests -v
```

(Os testes da v0.3 não fazem parte deste pacote simplificado de publicação; para eles, use o pacote da v0.3.)
