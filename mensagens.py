"""Adaptador de mensagens: formato comum para simulador e futuras integrações.

O WhatsApp oficial não está conectado aqui. Quando implementarmos o
webhook assinado, ele extrairá o telefone/texto e chamará esta função.
"""
from bot import processar_mensagem


def receber_mensagem(telefone: str, texto: str) -> str:
    """Conecta um canal de entrada ao núcleo de regras do bot.

    O canal (terminal, teste HTTP local, futuro webhook) não deve decidir
    quem é admin/motorista: essa autorização ocorre no núcleo via banco.
    Este método pressupõe que o canal autentique a ORIGEM quando necessário.
    """
    return processar_mensagem(telefone, texto)
