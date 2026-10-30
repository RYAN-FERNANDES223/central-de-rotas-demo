# Plano de evolução: do protótipo ao sistema comercial

Este documento distingue **o que a demonstração já faz**, **as informações levantadas** e **o que ainda depende de definição e aprovação da empresa**.

## 1. Implementado na demonstração

- [x] Interface visual em Streamlit.
- [x] Simulação de atendimento por chat.
- [x] Registro de solicitações com origem, destino, data e horário.
- [x] Diferenciação entre cliente, motorista e administrador no cenário de teste.
- [x] Aceite de rota com prevenção de dupla atribuição.
- [x] Acompanhamento de status e administração básica.
- [x] Testes automatizados no GitHub.

## 2. Informações iniciais do levantamento para a operação comercial

Esses pontos foram descritos como **características da empresa**, mas **não estão implementados no protótipo**:

| Aspecto | Informação levantada |
| --- | --- |
| Setor de atividade | Coleta, reciclagem de materiais e destinação de resíduos sólidos |
| Público 1 | Pessoas que solicitam coleta residencial de recicláveis, sem cobrança pelo recolhimento |
| Público 2 | Empresas que contratam coleta remunerada |
| Frota atual | Dois caminhões |
| Planejamento | Cada caminhão possui sua rota; algumas rotas são fixas |
| Atendimento | O bot receberá os contatos e solicitará nome e endereço de coleta |
| Materiais | O solicitante informará tipo e quantidade de materiais |

**Importante:** o levantamento está em andamento. Não são especificações finais nem autorização para implantar cada item da tabela.

## 3. Questões em aberto para o projeto comercial

- Quais materiais e resíduos são aceitos, rejeitados ou exigem análise especial?
- Como o cliente informa quantidade (kg, m³, sacos, unidades, estimativa)?
- Como distinguir coleta gratuita e serviço pago no atendimento e na operação?
- Quem define preço, orçamento, aprovação, contrato e condições de pagamento?
- Como são programados os dois caminhões e as rotas fixas? Quem decide encaixes e alterações?
- Há motorista fixo por caminhão? Como tratar substituições?
- Como se confirma a execução da coleta e como se registram imprevistos?
- Quais documentos ambientais, comprovantes ou integrações oficiais podem ser exigidos no caso concreto?
- Quais usuários terão acesso aos dados e qual será o prazo de retenção?
- Quais requisitos de disponibilidade, backup, proteção de dados e suporte devem ser contratados?

## 4. Proposta de fases, sujeita à aprovação

1. **Mapear processo atual:** entrevistas, exemplos reais de operação sem transferir dados pessoais para o repositório e definição de responsabilidades.
2. **Especificar requisitos:** fluxos de cliente gratuito, cliente pagante, programação da frota, administração, relatórios e exceções.
3. **Projetar arquitetura de produção:** autenticação, armazenamento centralizado, integrações, backup e segurança.
4. **Implementar por módulos:** receber solicitações, organizar coletas, distribuir trabalho e acompanhar execução.
5. **Validar:** testes funcionais, testes de acesso, cenário de duas coletas simultâneas e testes com usuários internos.
6. **Implantar e treinar:** homologação, treinamento, manuais e rotina de suporte.

A versão comercial deve manter **código, dados e credenciais próprios** em ambiente adequado. Este repositório público deve continuar apenas como **demonstração técnica e portfólio**.

[Voltar ao README](../README.md)
