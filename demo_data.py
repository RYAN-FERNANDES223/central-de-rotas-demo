"""Preparação do cenário FICTÍCIO. Nunca reutilize as contas simuladas em produção."""
from datetime import date, timedelta

from banco import preparar_banco, criar_admin_local
from mensagens import receber_mensagem

PERFIS = {
    'Cliente': '5500000000003',
    'Motorista A': '5500000000002',
    'Motorista B': '5500000000004',
    'Administrador': '5500000000001',
}


def enviar(nome_perfil, texto):
    return receber_mensagem(PERFIS[nome_perfil], texto)


def preparar_cenario():
    preparar_banco()
    criar_admin_local(PERFIS['Administrador'])
    assert 'cadastrado' in enviar('Administrador', '/motorista adicionar 5500000000002 Motorista A').lower()
    assert 'cadastrado' in enviar('Administrador', '/motorista adicionar 5500000000004 Motorista B').lower()

    exemplos = [
        ('Belo Horizonte, MG', 'Sete Lagoas, MG', 2, '08:00', 'Entrega de caixas (exemplo fictício)'),
        ('Contagem, MG', 'Betim, MG', 4, '13:30', 'Coleta de mercadorias (exemplo fictício)'),
    ]
    for origem, destino, dias, hora, observacoes in exemplos:
        mensagens = ['/nova', origem, destino,
                     (date.today() + timedelta(days=dias)).strftime('%d/%m/%Y'),
                     hora, observacoes, 's']
        for mensagem in mensagens:
            resposta = enviar('Cliente', mensagem)
        assert 'cadastrada' in resposta.lower(), resposta
