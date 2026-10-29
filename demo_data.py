"""Cenário fictício para demonstração. Nunca inserir CPFs de pessoas reais."""
from datetime import date, timedelta
from banco import preparar_banco, criar_admin_local
from mensagens import receber_mensagem

PERFIS = {
    'Cliente': '5500000000003',
    'Motorista A': '5500000000002',
    'Motorista B': '5500000000004',
    'Administrador': '5500000000001',
}

# Somente identidades de TESTE. São exemplos matematicamente válidos,
# mas NÃO constituem documentos de identidade reais ou contas verificadas.
CPFS_TESTE = {
    'Motorista A': '123.456.789-09',
    'Motorista B': '987.654.321-00',
    'Cliente Exemplo': '246.813.579-28',
    'Cliente visitante': '314.159.265-90',
}


def enviar(nome_perfil, texto):
    return receber_mensagem(PERFIS[nome_perfil], texto)


def preparar_cenario():
    preparar_banco()
    criar_admin_local(PERFIS['Administrador'])

    # O administrador pré-cadastra motoristas; eles só recebem permissão
    # após informar nome e CPF correto na própria conversa.
    for nome_perfil in ('Motorista A', 'Motorista B'):
        assert 'nome' in enviar('Administrador', '/motorista adicionar').lower()
        assert 'cpf' in enviar('Administrador', nome_perfil).lower()
        resposta = enviar('Administrador', CPFS_TESTE[nome_perfil])
        assert 'cadastrado' in resposta.lower(), resposta

    # Rotas de exemplo pertencem a um terceiro cliente fictício.
    telefone_exemplo = '5500000000005'
    assert 'nome' in receber_mensagem(telefone_exemplo, 'oi').lower()
    assert 'cpf' in receber_mensagem(telefone_exemplo, 'Cliente Exemplo').lower()
    resposta = receber_mensagem(telefone_exemplo, CPFS_TESTE['Cliente Exemplo'])
    assert '/nova' in resposta, resposta

    exemplos = [
        ('Belo Horizonte, MG', 'Sete Lagoas, MG', 2, '08:00',
         'Entrega de caixas (exemplo fictício)'),
        ('Contagem, MG', 'Betim, MG', 4, '13:30',
         'Coleta de mercadorias (exemplo fictício)'),
    ]
    for origem, destino, dias, hora, observacoes in exemplos:
        mensagens = [
            '/nova', origem, destino,
            (date.today() + timedelta(days=dias)).strftime('%d/%m/%Y'),
            hora, observacoes, 's'
        ]
        for mensagem in mensagens:
            resposta = receber_mensagem(telefone_exemplo, mensagem)
        assert 'cadastrada' in resposta.lower(), resposta
