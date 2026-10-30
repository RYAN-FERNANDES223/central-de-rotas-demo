# 🚚 Central de Rotas

**Protótipo de atendimento e gerenciamento de solicitações de transporte e coleta.**

[![Testes do bot](https://github.com/RZ223-ai/central-de-rotas-demo/actions/workflows/testes.yml/badge.svg)](https://github.com/RZ223-ai/central-de-rotas-demo/actions/workflows/testes.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/status-demonstra%C3%A7%C3%A3o-0F766E)

**[▶ Testar a demonstração online](https://central-de-rotas-demo-5t2wc5wrgla9jndvmvjxdn.streamlit.app/)** · [Ver roteiro de teste](docs/DEMONSTRACAO.md) · [Entender a arquitetura](docs/ARQUITETURA.md)

> **Atenção:** este projeto é uma **demonstração pública**. Não está integrado ao WhatsApp e **não deve ser utilizado em operações reais nem receber dados pessoais verdadeiros**.

## O problema e a proposta

Organizações que recebem solicitações de transporte ou coleta por mensagens precisam registrar pedidos, consultar serviços disponíveis, distribuir responsabilidades e acompanhar seu andamento.

A **Central de Rotas** demonstra como automatizar parte desse fluxo com um motor de regras em Python e uma interface web que simula conversas. O projeto também serve como base de estudos para soluções de atendimento e operações logísticas, incluindo cenários de coleta de recicláveis.

## O que já funciona

- **Atendimento guiado:** saudação, identificação demonstrativa e menus por perfil.
- **Cadastro de rota:** origem, destino, data, horário, observações e confirmação.
- **Motoristas:** pré-cadastro pelo administrador e acesso ao menu específico no simulador.
- **Aceite de serviço:** atribuição condicionada à disponibilidade da rota para impedir que dois motoristas assumam o mesmo pedido.
- **Acompanhamento:** listagens de rotas disponíveis, atribuídas, em andamento e concluídas.
- **Administração:** consulta da operação, cadastro/bloqueio de motoristas e liberação de rotas atribuídas.
- **Testes automatizados:** validações executadas pelo GitHub Actions.

A interface utiliza perfis e CPFs **fictícios** para demonstrar os diferentes papéis. A checagem matemática de um CPF **não confirma identidade** e não é uma solução de autenticação real.

## Tecnologias e organização

| Tecnologia | Utilização |
| --- | --- |
| **Python** | Regras de negócio e fluxo das conversas |
| **Streamlit** | Demonstração visual interativa |
| **SQLite** | Persistência temporária por sessão no protótipo |
| **GitHub Actions + unittest** | Verificação automática de sintaxe e testes |

```text
central-de-rotas-demo/
├── streamlit_app.py          # Interface de demonstração
├── bot.py                    # Atendimento e regras de negócio
├── banco.py                  # Estrutura e operações do SQLite
├── identidade.py             # Identificação fictícia para testes
├── mensagens.py              # Entrada de mensagens simuladas
├── demo_data.py              # Cenário de exemplo
├── tests/                    # Testes automatizados
├── docs/                     # Documentação técnica e evolução
└── .github/workflows/        # Automação de testes
```

## Executar localmente

**Pré-requisito:** Python instalado.

No Windows, abra o terminal do VS Code na pasta do projeto:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

No Linux/macOS, ative o ambiente virtual com `source .venv/bin/activate` e utilize `python` no lugar de `py`.

Para executar os testes:

```bash
python -m unittest discover -s tests -v
```

## Limites do protótipo

- **Não** envia nem recebe mensagens reais do WhatsApp.
- **Não** oferece autenticação robusta de usuários; a seleção de perfis é simulada.
- Cada visitante possui um banco SQLite temporário próprio; **as sessões não compartilham rotas**.
- Os documentos de CPF apresentados nos testes são somente números fictícios para validar o fluxo.
- **Não** implementa ainda planejamento de frota, rotas fixas, cobrança, classificação de resíduos ou documentos ambientais.
- A implantação comercial requer arquitetura e controles de segurança próprios.

## Próximos passos

A evolução para uso comercial deve ser desenvolvida separadamente, após definição de requisitos e autorização do cliente. Entre as frentes previstas para avaliação estão a integração oficial com o WhatsApp, autenticação adequada, banco persistente, gestão de solicitações de coleta, planejamento da frota e treinamento dos usuários.

Consulte o [plano de evolução](docs/PLANO_DE_EVOLUCAO.md) para separar o que **existe**, o que foi **levantado** e o que ainda precisa ser **definido**.

## Documentação

- [Demonstração passo a passo](docs/DEMONSTRACAO.md)
- [Arquitetura e regras de negócio](docs/ARQUITETURA.md)
- [Plano de evolução](docs/PLANO_DE_EVOLUCAO.md)
- [Cuidados de segurança](SECURITY.md)

---

**Desenvolvimento:** [RZ223-ai](https://github.com/RZ223-ai) · Projeto autoral em evolução.

**Licença:** ainda não foi definida uma licença de reutilização ou redistribuição. A publicação do código não concede, por si só, autorização para uso comercial por terceiros.
