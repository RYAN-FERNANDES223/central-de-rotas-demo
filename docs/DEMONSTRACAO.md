# Guia de demonstração da Central de Rotas

Este guia apresenta o protótipo para possíveis clientes sem utilizar informações reais.

**[Abrir demonstração online](https://central-de-rotas-demo-5t2wc5wrgla9jndvmvjxdn.streamlit.app/)**

> Não use nomes, telefones, endereços ou CPFs de pessoas reais. O aplicativo é público, não autentica visitantes e não se conecta ao WhatsApp.

## 1. Inicie do zero

Abra o site e clique em **Reiniciar demonstração**, se necessário. Escolha o perfil **Cliente**. O bot apresentará uma saudação e solicitará o nome e um CPF de teste.

- Nome fictício: `Maria Exemplo`
- CPF exclusivamente para teste: `314.159.265-90`

Após o preenchimento, o bot exibirá o menu do cliente.

## 2. Cadastre uma rota

No chat, utilize `/nova`, preencha origem e destino **fictícios**, informe uma data futura no formato `DD/MM/AAAA`, um horário `HH:MM` e uma observação. Confirme com `S`.

A nova rota ficará disponível no banco temporário dessa sessão.

## 3. Identifique um motorista

Selecione **Motorista A** no menu lateral e converse com o bot.

- Nome: `Motorista A`
- CPF somente para teste: `123.456.789-09`

O bot verificará se existe pré-cadastro com esses dados. Quando corresponderem, abrirá o menu do motorista.

O **Motorista B** também está pré-cadastrado:

- Nome: `Motorista B`
- CPF somente para teste: `987.654.321-00`

## 4. Aceite e acompanhe

Com o perfil **Motorista A**, use `/rotas` ou os cartões da interface para consultar as rotas disponíveis. Clique em **Aceitar rota** para assumir um serviço.

Troque para **Motorista B**. A rota assumida por A não deverá estar disponível para novo aceite. O comando `/aceitar ID` da rota já assumida deve ser recusado.

Retorne ao perfil **Motorista A** para testar `/iniciar ID` e `/concluir ID`.

## 5. Acompanhe como administrador

Selecione o perfil **Administrador** e use:

| Comando | Função |
| --- | --- |
| `/resumo` | Resumo das rotas |
| `/rotas` | Listagem de rotas |
| `/motoristas` | Lista dos motoristas pré-cadastrados |
| `/motorista adicionar` | Abre cadastro guiado de nome e CPF fictício |
| `/motorista bloquear ID` | Bloqueia motorista pelo código |
| `/motorista ativar ID` | Reativa motorista |
| `/liberar ID` | Devolve rota atribuída à lista de disponíveis |

**Observação:** o perfil de administrador é livremente selecionável no simulador. Isso é intencional na demonstração, mas não seria aceitável na produção.

## Limitações do cenário

- As rotas e os motoristas de exemplo são gerados com informações artificiais.
- A seleção de perfil na interface simula contatos distintos; não é um login real.
- O nome e CPF não validam a identidade; a verificação é apenas de consistência e cadastro fictício.
- O histórico de mensagens oculta o CPF na exibição, mas não torna o chat um ambiente apropriado para documentos reais.
- Os registros são temporários e isolados por visitante.
- O sistema comercial terá fluxo diferente, a ser definido no levantamento operacional.

[Voltar ao README](../README.md)
