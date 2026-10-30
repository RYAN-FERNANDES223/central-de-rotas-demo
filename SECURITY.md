# Segurança e uso responsável

## Escopo

A **Central de Rotas** publicada neste repositório é um protótipo educacional e de apresentação comercial. Os dados são fictícios e a autenticação é simulada.

## Dados pessoais

- Não informe CPF real, nome completo real, telefone real, endereço residencial real nem informações de clientes.
- Os CPFs encontrados no código servem exclusivamente para demonstrar validação matemática. Eles não provam identidade.
- Os dados do protótipo são salvos em banco SQLite temporário por sessão. Esse mecanismo não atende aos requisitos de armazenamento, privacidade ou disponibilidade de um sistema comercial.
- A chave de assinatura demonstrativa do CPF é conhecida no código público: **não é um segredo de produção**.

## Credenciais e informações da contratante

**Nunca** publique senhas, tokens da API do WhatsApp, arquivos `.env`, dumps de bancos, contratos, documentos ambientais ou informações operacionais não autorizadas.

O código comercial e a documentação interna de clientes devem ficar em repositório **privado**, com permissões restritas e gestão de segredos própria.

## Acesso e autenticação

Nome e CPF não são fatores de autenticação suficientes para motoristas ou administradores. O sistema definitivo exigirá mecanismos adicionais, incluindo verificação da origem das mensagens, autorização por perfil, proteção contra tentativas abusivas e trilhas de auditoria.

## Relatar problemas

Evite expor informações exploráveis em issues públicas. Entre em contato com o mantenedor por um canal privado antes de divulgar possíveis vulnerabilidades.

[Voltar ao README](README.md)
