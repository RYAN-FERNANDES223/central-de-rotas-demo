"""Regras e comandos. Recebe número/texto; devolve texto (independente do WhatsApp)."""
from datetime import datetime, date

from identidade import cpf_valido, assinatura_cpf, normalizar_nome, nome_valido
from banco import (conectar, preparar_banco, garantir_cliente, obter_usuario,
                   obter_conversa, salvar_conversa, limpar_conversa, agora)

AJUDA_CLIENTE = ('📋 Menu principal — Central de Rotas\n'
                 '➕ /nova — Solicitar uma rota\n'
                 '📦 /minhasrotas — Consultar minhas solicitações\n'
                 '❌ /cancelar — Cancelar um cadastro em andamento\n'
                 '❓ /ajuda — Mostrar este menu novamente')
AJUDA_MOTORISTA = ('Área do motorista:\n'
                   '/rotas — rotas disponíveis\n'
                   '/detalhes 101 — conferir dados de uma rota\n'
                   '/aceitar 101 — assumir uma rota\n'
                   '/minhas — minhas rotas\n'
                   '/iniciar 101 — iniciar a rota\n'
                   '/concluir 101 — finalizar a rota')
AJUDA_ADMIN = ('🔐 Área administrativa:\n'
              '/resumo — situação das rotas\n'
              '/rotas — consultar todas as rotas\n'
              '/detalhes 101 — consultar detalhes\n'
              '/motorista adicionar — cadastrar nome e CPF em etapas\n'
              '/motoristas — listar motoristas e seus códigos\n'
              '/motorista bloquear 1 — bloquear pelo código\n'
              '/motorista ativar 1 — reativar pelo código\n'
              '/cancelar — interromper cadastro de motorista\n'
              '/liberar 101 — devolver rota atribuída à lista')


def telefone_valido(telefone):
    return telefone.isdigit() and 10 <= len(telefone) <= 15


def extrair_id(partes):
    if len(partes) != 2 or not partes[1].isdigit() or int(partes[1]) <= 0:
        return None
    return int(partes[1])


def data_valida(texto):
    try:
        dia = datetime.strptime(texto, '%d/%m/%Y').date()
        if dia < date.today():
            return None
        return dia.isoformat()
    except ValueError:
        return None


def hora_valida(texto):
    try:
        return datetime.strptime(texto, '%H:%M').strftime('%H:%M')
    except ValueError:
        return None


def lista_rotas(conn, condicao='', params=()):
    sql = '''SELECT r.*, m.nome AS motorista_nome
             FROM rotas r LEFT JOIN motoristas m ON m.id=r.motorista_id'''
    if condicao:
        sql += ' WHERE ' + condicao
    sql += ' ORDER BY r.data ASC, r.horario ASC, r.id ASC LIMIT 20'
    return conn.execute(sql, params).fetchall()


def formatar_rota(r):
    try:
        data = date.fromisoformat(r['data']).strftime('%d/%m/%Y')
    except ValueError:
        data = r['data']
    return f"#{r['id']} | {r['origem']} → {r['destino']}\n{data} às {r['horario']} | {r['status']}"


def processo_cliente(conn, telefone, texto, etapa, dados):
    if etapa == 'origem':
        if len(texto) < 2 or len(texto) > 120:
            return 'Informe uma origem entre 2 e 120 caracteres.'
        dados['origem'] = texto
        salvar_conversa(conn, telefone, 'destino', dados)
        return 'Qual é o destino da rota?'

    if etapa == 'destino':
        if len(texto) < 2 or len(texto) > 120:
            return 'Informe um destino entre 2 e 120 caracteres.'
        dados['destino'] = texto
        salvar_conversa(conn, telefone, 'data', dados)
        return 'Qual é a data da rota? Use DD/MM/AAAA.'

    if etapa == 'data':
        data = data_valida(texto)
        if data is None:
            return 'Data inválida ou passada. Use DD/MM/AAAA e escolha hoje ou uma data futura.'
        dados['data'] = data
        salvar_conversa(conn, telefone, 'horario', dados)
        return 'Qual é o horário? Use HH:MM (por exemplo, 08:30).'

    if etapa == 'horario':
        horario = hora_valida(texto)
        if horario is None:
            return 'Horário inválido. Use HH:MM no formato de 24 horas.'
        dados['horario'] = horario
        salvar_conversa(conn, telefone, 'observacoes', dados)
        return 'Descreva a carga ou observações. Digite - se não houver observações.'

    if etapa == 'observacoes':
        if len(texto) > 500 or not texto:
            return 'A observação deve ter até 500 caracteres. Use - se não houver.'
        dados['observacoes'] = '' if texto == '-' else texto
        salvar_conversa(conn, telefone, 'confirmar', dados)
        return ('Confira sua rota:\n'
                f"Origem: {dados['origem']}\nDestino: {dados['destino']}\n"
                f"Data: {date.fromisoformat(dados['data']).strftime('%d/%m/%Y')}\n"
                f"Horário: {dados['horario']}\nObservações: {dados['observacoes'] or 'Nenhuma'}\n"
                'Confirma o cadastro? Responda S ou N.')

    if etapa == 'confirmar':
        if texto.casefold() in ('n', 'não', 'nao'):
            limpar_conversa(conn, telefone)
            return 'Cadastro cancelado. Use /nova para começar novamente.'
        if texto.casefold() != 's':
            return 'Responda S para confirmar ou N para cancelar.'
        cursor = conn.execute('''INSERT INTO rotas
             (origem,destino,data,horario,observacoes,criada_em,cliente_telefone)
             VALUES (?,?,?,?,?,?,?)''',
             (dados['origem'], dados['destino'], dados['data'], dados['horario'],
              dados['observacoes'], agora(), telefone))
        limpar_conversa(conn, telefone)
        return f'Rota #{cursor.lastrowid} cadastrada! Ela está disponível para os motoristas.'

    limpar_conversa(conn, telefone)
    return 'O cadastro foi reiniciado. Digite /nova.'


COMANDOS_RESTRITOS = {
    '/admin', '/motorista', '/rotas', '/detalhes', '/aceitar',
    '/minhas', '/iniciar', '/concluir', '/resumo', '/liberar'
}
NEGADO = ('Acesso negado. Este comando é exclusivo para motoristas '
          'ou administradores autorizados. Digite /ajuda para ver suas opções.')


def detalhes_rota(conn, rota_id, condicao_extra='', parametros=()):
    sql = '''SELECT id,origem,destino,data,horario,observacoes,status
             FROM rotas WHERE id=?'''
    if condicao_extra:
        sql += ' AND ' + condicao_extra
    rota = conn.execute(sql, (rota_id, *parametros)).fetchone()
    if rota is None:
        return 'Rota não encontrada ou sem permissão para consulta.'
    return (f"Rota #{rota['id']}\n"
            f"Origem: {rota['origem']}\n"
            f"Destino: {rota['destino']}\n"
            f"Data: {date.fromisoformat(rota['data']).strftime('%d/%m/%Y')}\n"
            f"Horário: {rota['horario']}\n"
            f"Observações: {rota['observacoes'] or 'Nenhuma'}\n"
            f"Status: {rota['status']}")


def comandos_cliente(conn, telefone, texto):
    """Primeiro nome, depois CPF fictício; apenas então define o perfil."""
    usuario = obter_usuario(conn, telefone)
    etapa, dados = obter_conversa(conn, telefone)
    comando = texto.casefold()
    primeira_palavra = comando.split()[0]

    # A identificação somente por nome+CPF é uma simulação, NÃO uma prova
    # de identidade. Produção exigirá confirmação do telefone e 2º fator.
    if not usuario['cpf_confirmado']:
        if etapa not in ('ident_nome', 'ident_cpf'):
            if usuario['nome_confirmado'] and usuario['nome'] != 'Cliente':
                salvar_conversa(conn, telefone, 'ident_cpf', {'nome': usuario['nome']})
                return (f'👋 Olá novamente, {usuario["nome"]}!\n'
                        'Para liberar seu menu, informe seu CPF (somente dados fictícios nesta demonstração).')
            salvar_conversa(conn, telefone, 'ident_nome', {})
            return ('👋 Olá! Seja bem-vindo à Central de Rotas!\n'
                    '🚚 Sou o assistente virtual da empresa.\n\n'
                    'Antes de começar, qual é seu nome?')

        if etapa == 'ident_nome':
            nome = ' '.join(texto.split())
            if not nome_valido(nome):
                return ('Nome inválido. Digite somente letras e espaços, '
                        'por exemplo: Maria Silva.')
            salvar_conversa(conn, telefone, 'ident_cpf', {'nome': nome})
            return (f'Obrigado, {nome}! 😊\n'
                    'Agora informe seu CPF para identificar o atendimento.\n'
                    '⚠️ Esta é uma demonstração: utilize apenas um CPF fictício com dígitos verificadores válidos.')

        # Etapa CPF: só guardamos a assinatura, nunca os dígitos no banco.
        if not cpf_valido(texto):
            return ('CPF inválido. Confira os 11 dígitos e tente novamente.\n'
                    'Utilize somente números fictícios nesta demonstração.')
        assinatura = assinatura_cpf(texto)
        nome = dados['nome']
        motorista = conn.execute('SELECT id, nome, ativo FROM motoristas WHERE cpf_hash=?',
                                 (assinatura,)).fetchone()
        if motorista:
            if not motorista['ativo']:
                return 'Cadastro de motorista bloqueado. Entre em contato com a administração.'
            if normalizar_nome(motorista['nome']) != normalizar_nome(nome):
                return ('O nome e o CPF não correspondem ao cadastro de motorista.\n'
                        'Confira os dados ou procure a administração.')
            vinculo = conn.execute(
                'SELECT telefone FROM usuarios WHERE motorista_id=? AND telefone<>?',
                (motorista['id'], telefone)
            ).fetchone()
            if vinculo:
                return ('Este cadastro de motorista já foi vinculado a outro contato. '
                        'Procure a administração.')
            conn.execute('''UPDATE usuarios SET nome=?, nome_confirmado=1,
                            cpf_hash=?, cpf_confirmado=1, papel='motorista',
                            motorista_id=?, ativo=1 WHERE telefone=? AND papel='cliente' ''',
                         (motorista['nome'], assinatura, motorista['id'], telefone))
            limpar_conversa(conn, telefone)
            return (f'✅ Identificação de motorista concluída, {motorista["nome"]}!\n'
                    f'\n{AJUDA_MOTORISTA}')

        conn.execute('''UPDATE usuarios SET nome=?, nome_confirmado=1,
                        cpf_hash=?, cpf_confirmado=1 WHERE telefone=? AND papel='cliente' ''',
                     (nome, assinatura, telefone))
        limpar_conversa(conn, telefone)
        return (f'✅ Cadastro de demonstração concluído, {nome}! 😊\n'
                'CPF conferido apenas quanto ao formato e dígitos verificadores.\n\n'
                f'{AJUDA_CLIENTE}')

    if primeira_palavra in COMANDOS_RESTRITOS or primeira_palavra == '/motoristas':
        return NEGADO
    if comando == '/cancelar':
        limpar_conversa(conn, telefone)
        return 'Cadastro cancelado. Digite /nova quando quiser.'
    if comando == '/nova':
        salvar_conversa(conn, telefone, 'origem', {})
        return 'Vamos cadastrar uma rota. Qual é a origem?'
    if etapa is not None:
        return processo_cliente(conn, telefone, texto, etapa, dados)
    if comando == '/minhasrotas':
        rotas = lista_rotas(conn, 'r.cliente_telefone=?', (telefone,))
        return ('Suas rotas:\n' + '\n\n'.join(map(formatar_rota, rotas))) if rotas else 'Nenhuma rota encontrada.'
    return f'Olá, {usuario["nome"]}! 👋\n\n{AJUDA_CLIENTE}'


def comandos_motorista(conn, usuario, texto):
    partes = texto.split()
    comando = partes[0].casefold()
    motorista_id = usuario['motorista_id']
    if comando in ('/motorista', '/ajuda', 'oi', 'olá', 'ola'):
        return AJUDA_MOTORISTA
    if comando == '/detalhes':
        rota_id = extrair_id(partes)
        if rota_id is None:
            return 'Uso correto: /detalhes 101'
        # Para reduzir exposição, motorista pode consultar apenas rotas
        # disponíveis ou rotas que ele próprio assumiu.
        return detalhes_rota(conn, rota_id,
            "(status='disponivel' OR motorista_id=?)", (motorista_id,))
    if comando == '/rotas':
        rotas = lista_rotas(conn, "r.status='disponivel'")
        if not rotas:
            return 'Não há rotas disponíveis no momento.'
        return 'Rotas disponíveis:\n' + '\n\n'.join(map(formatar_rota, rotas)) + '\n\nPara aceitar: /aceitar ID'
    if comando == '/minhas':
        rotas = lista_rotas(conn, 'r.motorista_id=?', (motorista_id,))
        return ('Minhas rotas:\n' + '\n\n'.join(map(formatar_rota, rotas))) if rotas else 'Você ainda não assumiu nenhuma rota.'
    if comando in ('/aceitar', '/iniciar', '/concluir'):
        rota_id = extrair_id(partes)
        if rota_id is None:
            return f'Uso correto: {comando} 101'
        if comando == '/aceitar':
            # UPDATE condicionado + transação SQLite: exatamente um aceite vence.
            cursor = conn.execute('''UPDATE rotas SET status='atribuida',
                 motorista_id=?, assumida_em=?
                 WHERE id=? AND status='disponivel' ''',
                 (motorista_id, agora(), rota_id))
            return (f'Rota #{rota_id} atribuída a você!'
                    if cursor.rowcount == 1 else
                    'Rota não encontrada ou já indisponível.')
        if comando == '/iniciar':
            cursor = conn.execute('''UPDATE rotas SET status='em_andamento'
                 WHERE id=? AND motorista_id=? AND status='atribuida' ''',
                 (rota_id, motorista_id))
            return (f'Rota #{rota_id} iniciada.' if cursor.rowcount == 1
                    else 'Não é possível iniciar esta rota.')
        cursor = conn.execute('''UPDATE rotas SET status='concluida'
             WHERE id=? AND motorista_id=? AND status IN ('atribuida','em_andamento')''',
             (rota_id, motorista_id))
        return (f'Rota #{rota_id} concluída.' if cursor.rowcount == 1
                else 'Não é possível concluir esta rota.')
    if comando in ('/admin', '/resumo', '/liberar') or comando == '/nova':
        return 'Acesso negado. Este comando não pertence ao perfil de motorista.'
    return AJUDA_MOTORISTA


def comandos_admin(conn, texto, telefone):
    """Administrador cadastra motoristas por nome e CPF em duas mensagens."""
    partes = texto.split()
    comando = partes[0].casefold()
    etapa, dados = obter_conversa(conn, telefone)

    if comando == '/cancelar':
        limpar_conversa(conn, telefone)
        return 'Operação administrativa cancelada.'

    if etapa == 'admin_motorista_nome':
        nome = ' '.join(texto.split())
        if not nome_valido(nome):
            return 'Digite o nome do motorista usando letras (2 a 80 caracteres).'
        salvar_conversa(conn, telefone, 'admin_motorista_cpf', {'nome': nome})
        return (f'Nome informado: {nome}.\n'
                'Agora informe o CPF fictício desse motorista (11 dígitos).')

    if etapa == 'admin_motorista_cpf':
        if not cpf_valido(texto):
            return 'CPF inválido. Confira os dígitos verificadores ou digite /cancelar.'
        assinatura = assinatura_cpf(texto)
        existente = conn.execute(
            'SELECT id FROM motoristas WHERE cpf_hash=?', (assinatura,)
        ).fetchone()
        if existente:
            return ('Já existe um motorista cadastrado com esse CPF. '
                    'Informe outro ou digite /cancelar.')
        try:
            cursor = conn.execute(
                'INSERT INTO motoristas(nome,cpf_hash,ativo) VALUES(?,?,1)',
                (dados['nome'], assinatura)
            )
        except Exception:
            # A transação será revertida pelo gerenciador do banco.
            raise
        limpar_conversa(conn, telefone)
        return (f'✅ Motorista {dados["nome"]} cadastrado! Código #{cursor.lastrowid}.\n'
                'Ele poderá informar nome e CPF no primeiro contato para abrir o menu exclusivo.')

    if comando in ('/admin', '/ajuda', 'oi', 'olá', 'ola'):
        return AJUDA_ADMIN
    if comando == '/detalhes':
        rota_id = extrair_id(partes)
        if rota_id is None:
            return 'Uso correto: /detalhes 101'
        return detalhes_rota(conn, rota_id)
    if comando == '/rotas':
        rotas = lista_rotas(conn)
        return ('Rotas:\n' + '\n\n'.join(map(formatar_rota, rotas))) if rotas else 'Nenhuma rota cadastrada.'
    if comando == '/resumo':
        linhas = conn.execute('SELECT status,COUNT(*) total FROM rotas GROUP BY status').fetchall()
        return ('Resumo de rotas:\n' + '\n'.join(f"{r['status']}: {r['total']}" for r in linhas)) if linhas else 'Não há rotas registradas.'
    if comando == '/motoristas':
        linhas = conn.execute(
            'SELECT id,nome,ativo FROM motoristas WHERE cpf_hash IS NOT NULL ORDER BY id'
        ).fetchall()
        if not linhas:
            return 'Nenhum motorista cadastrado com CPF nesta demonstração.'
        return ('Motoristas cadastrados:\n' +
                '\n'.join(f"#{r['id']} — {r['nome']} — " +
                          ('ativo' if r['ativo'] else 'bloqueado') for r in linhas))

    if comando == '/motorista':
        if len(partes) >= 2 and partes[1].casefold() == 'adicionar':
            if len(partes) != 2:
                return 'Use apenas /motorista adicionar. Vou perguntar nome e CPF em seguida.'
            salvar_conversa(conn, telefone, 'admin_motorista_nome', {})
            return ('🚚 Cadastro de motorista iniciado.\n'
                    'Qual é o nome completo do motorista?')
        if len(partes) != 3 or partes[1].casefold() not in ('bloquear', 'ativar'):
            return ('Use /motorista adicionar, /motoristas, '
                    '/motorista bloquear ID ou /motorista ativar ID.')
        acao = partes[1].casefold()
        if not partes[2].isdigit() or int(partes[2]) <= 0:
            return f'Uso correto: /motorista {acao} 1'
        motorista_id = int(partes[2])
        registro = conn.execute(
            'SELECT id FROM motoristas WHERE id=? AND cpf_hash IS NOT NULL',
            (motorista_id,)
        ).fetchone()
        if not registro:
            return 'Motorista não encontrado.'
        ativo = 0 if acao == 'bloquear' else 1
        conn.execute('UPDATE motoristas SET ativo=? WHERE id=?', (ativo, motorista_id))
        conn.execute("UPDATE usuarios SET ativo=? WHERE motorista_id=? AND papel='motorista'",
                     (ativo, motorista_id))
        return 'Motorista bloqueado.' if not ativo else 'Motorista reativado.'

    if comando == '/liberar':
        rota_id = extrair_id(partes)
        if rota_id is None:
            return 'Uso correto: /liberar 101'
        cursor = conn.execute('''UPDATE rotas
            SET status='disponivel', motorista_id=NULL, assumida_em=NULL
            WHERE id=? AND status='atribuida' ''', (rota_id,))
        return (f'Rota #{rota_id} novamente disponível.' if cursor.rowcount == 1
                else 'Só é possível liberar uma rota atribuída.')
    if comando in ('/aceitar', '/iniciar', '/concluir', '/nova'):
        return 'Acesso negado. Este comando não pertence ao perfil administrador.'
    return AJUDA_ADMIN


def processar_mensagem(telefone, texto):
    """Ponto de entrada do bot; simula o corpo de uma mensagem validada do WhatsApp.

    A verificação de autenticidade do webhook AINDA NÃO foi implementada.
    Jamais expor esta função diretamente como uma API pública com telefone arbitrário.
    """
    telefone = str(telefone).strip()
    texto = str(texto).strip()
    if not telefone_valido(telefone):
        return 'Identificador de telefone inválido.'
    if not texto:
        return 'Envie uma mensagem ou um comando.'
    usuario = garantir_cliente(telefone)
    if not usuario['ativo']:
        return 'Acesso bloqueado. Contate a administração.'
    with conectar() as conn:
        # Reserva o banco antes de verificar/aceitar a rota: evita
        # conflito quando dois motoristas tentam aceitar ao mesmo tempo.
        if texto.split()[0].casefold() == '/aceitar':
            conn.execute('BEGIN IMMEDIATE')
        usuario = obter_usuario(conn, telefone)
        if usuario['papel'] == 'admin':
            return comandos_admin(conn, texto, telefone)
        if usuario['papel'] == 'motorista':
            return comandos_motorista(conn, usuario, texto)
        return comandos_cliente(conn, telefone, texto)
