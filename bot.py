"""Regras e comandos. Recebe número/texto; devolve texto (independente do WhatsApp)."""
from datetime import datetime, date
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
AJUDA_ADMIN = ('Área administrativa:\n'
              '/resumo — quantidade de rotas por status\n'
              '/rotas — consultar rotas\n'
              '/detalhes 101 — consultar dados de uma rota\n'
              '/motorista adicionar 5500000000002 Nome — cadastrar\n'
              '/motorista bloquear 5500000000002 — bloquear acesso\n'
              '/motorista ativar 5500000000002 — reativar acesso\n'
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
    usuario = obter_usuario(conn, telefone)
    etapa, dados = obter_conversa(conn, telefone)
    comando = texto.casefold()

    # Primeiro contato: solicitamos o nome antes de mostrar qualquer menu.
    # Esta etapa fica salva no banco, de forma que o atendimento possa
    # continuar caso o visitante recarregue a página.
    if not usuario['nome_confirmado']:
        if etapa != 'nome':
            salvar_conversa(conn, telefone, 'nome', {})
            return ('👋 Olá! Seja bem-vindo à Central de Rotas!\n'
                    '🚚 Sou o assistente virtual da empresa.\n\n'
                    'Antes de começarmos, como posso chamar você?')

        nome = ' '.join(texto.split())
        if (not 2 <= len(nome) <= 80 or nome.startswith('/')
                or not any(letra.isalpha() for letra in nome)
                or any(not (letra.isalpha() or letra in " -'’") for letra in nome)):
            return ('Não consegui identificar seu nome. 😊\n'
                    'Por favor, digite seu nome com letras, por exemplo: Maria Silva.')

        conn.execute("""UPDATE usuarios
                        SET nome=?, nome_confirmado=1
                        WHERE telefone=? AND papel='cliente'""", (nome, telefone))
        limpar_conversa(conn, telefone)
        return f'Prazer em conhecer você, {nome}! 😊\n\n{AJUDA_CLIENTE}'

    primeira_palavra = comando.split()[0]
    if primeira_palavra in COMANDOS_RESTRITOS:
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


def comandos_admin(conn, texto):
    partes = texto.split()
    comando = partes[0].casefold()
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
    if comando == '/liberar':
        rota_id = extrair_id(partes)
        if rota_id is None:
            return 'Uso correto: /liberar 101'
        cursor = conn.execute('''UPDATE rotas
            SET status='disponivel', motorista_id=NULL, assumida_em=NULL
            WHERE id=? AND status='atribuida' ''', (rota_id,))
        return (f'Rota #{rota_id} novamente disponível.' if cursor.rowcount == 1
                else 'Só é possível liberar uma rota atribuída.')
    if comando == '/motorista':
        if len(partes) < 3:
            return 'Use /motorista adicionar TELEFONE NOME, /motorista bloquear TELEFONE ou /motorista ativar TELEFONE.'
        acao = partes[1].casefold()
        numero = partes[2]
        if not telefone_valido(numero):
            return 'Número inválido: use DDI + DDD + telefone, somente dígitos.'
        existente = obter_usuario(conn, numero)
        if acao == 'adicionar':
            nome = ' '.join(partes[3:]).strip()
            if not 2 <= len(nome) <= 100:
                return 'Uso correto: /motorista adicionar 5531999999999 Nome Sobrenome'
            if existente and existente['papel'] != 'cliente':
                return 'Este número já é motorista ou administrador.'
            cur = conn.execute('INSERT INTO motoristas(nome) VALUES (?)', (nome,))
            if existente:
                # Apenas o administrador pode promover um cliente existente.
                conn.execute('''UPDATE usuarios SET nome=?, papel='motorista',
                    motorista_id=?, ativo=1 WHERE telefone=? AND papel='cliente' ''',
                    (nome, cur.lastrowid, numero))
                limpar_conversa(conn, numero)
            else:
                conn.execute('''INSERT INTO usuarios(telefone,nome,papel,motorista_id)
                    VALUES (?,?,'motorista',?)''', (numero, nome, cur.lastrowid))
            return f'Motorista {nome} cadastrado e autorizado.'
        if acao in ('bloquear', 'ativar'):
            if len(partes) != 3:
                return f'Uso correto: /motorista {acao} TELEFONE'
            if not existente or existente['papel'] != 'motorista':
                return 'Motorista não encontrado.'
            ativo = 0 if acao == 'bloquear' else 1
            conn.execute('UPDATE usuarios SET ativo=? WHERE telefone=?', (ativo, numero))
            return 'Motorista bloqueado.' if not ativo else 'Motorista reativado.'
        return 'Ação inválida. Use adicionar, bloquear ou ativar.'
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
            return comandos_admin(conn, texto)
        if usuario['papel'] == 'motorista':
            return comandos_motorista(conn, usuario, texto)
        return comandos_cliente(conn, telefone, texto)
