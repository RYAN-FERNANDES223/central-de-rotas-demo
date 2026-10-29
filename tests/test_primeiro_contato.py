"""Testes de identificação e permissões da demonstração 0.7.

Use CPF fictício de teste, nunca documentos de pessoas reais.
"""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from banco import conectar, criar_admin_local, preparar_banco, selecionar_banco
from identidade import cpf_valido
from mensagens import receber_mensagem

CLIENTE = "5500000000003"
MOTORISTA_A = "5500000000002"
MOTORISTA_B = "5500000000004"
ADMIN = "5500000000001"
OUTRO = "5500000000006"
CPF_A = "123.456.789-09"
CPF_B = "987.654.321-00"
CPF_CLIENTE = "314.159.265-90"


def registrar_motorista(nome, cpf):
    assert 'nome' in receber_mensagem(ADMIN, '/motorista adicionar').lower()
    assert 'cpf' in receber_mensagem(ADMIN, nome).lower()
    return receber_mensagem(ADMIN, cpf)


def identificar(telefone, nome, cpf):
    primeiro = receber_mensagem(telefone, "oi")
    segundo = receber_mensagem(telefone, nome)
    terceiro = receber_mensagem(telefone, cpf)
    return primeiro, segundo, terceiro


class IdentificacaoTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="rotas_id_")
        selecionar_banco(Path(self.pasta.name) / "rotas.db")
        preparar_banco()
        criar_admin_local(ADMIN)

    def tearDown(self):
        self.pasta.cleanup()

    def test_digitos_verificadores(self):
        self.assertTrue(cpf_valido(CPF_A))
        self.assertTrue(cpf_valido(CPF_B))
        self.assertTrue(cpf_valido(CPF_CLIENTE))
        self.assertFalse(cpf_valido("000.000.000-00"))
        self.assertFalse(cpf_valido("123.456.789-00"))
        self.assertFalse(cpf_valido("123ABC78909"))

    def test_cliente_precisa_nome_e_cpf(self):
        primeira = receber_mensagem(CLIENTE, "oi")
        self.assertIn("nome", primeira.lower())
        self.assertNotIn("/nova", primeira)

        self.assertIn("nome inválido", receber_mensagem(CLIENTE, "/nova").lower())
        self.assertIn("cpf", receber_mensagem(CLIENTE, "Maria Silva").lower())
        self.assertIn("cpf inválido", receber_mensagem(CLIENTE, "123").lower())

        menu = receber_mensagem(CLIENTE, CPF_CLIENTE)
        self.assertIn("/nova", menu)
        self.assertIn("Maria Silva", menu)
        with conectar() as conn:
            registro = conn.execute("SELECT nome,papel,cpf_hash,cpf_confirmado "
                                    "FROM usuarios WHERE telefone=?", (CLIENTE,)).fetchone()
        self.assertEqual(registro["papel"], "cliente")
        self.assertEqual(registro["nome"], "Maria Silva")
        self.assertEqual(registro["cpf_confirmado"], 1)
        self.assertNotEqual(registro["cpf_hash"], CPF_CLIENTE.replace(".", "").replace("-", ""))
        self.assertIn("origem", receber_mensagem(CLIENTE, "/nova").lower())

    def test_motorista_precisa_ser_pre_cadastrado(self):
        nome, cpf = "Motorista A", CPF_A
        self.assertIn("cadastrado", registrar_motorista(nome, cpf).lower())
        inicial, segundo, final = identificar(MOTORISTA_A, "motorista a", cpf)
        self.assertIn("nome", inicial.lower())
        self.assertIn("cpf", segundo.lower())
        self.assertIn("/aceitar", final)
        with conectar() as conn:
            registro = conn.execute("SELECT papel,cpf_confirmado,motorista_id FROM usuarios WHERE telefone=?",
                                    (MOTORISTA_A,)).fetchone()
        self.assertEqual(registro["papel"], "motorista")
        self.assertEqual(registro["cpf_confirmado"], 1)
        self.assertIsNotNone(registro["motorista_id"])
        self.assertNotIn("acesso negado", receber_mensagem(MOTORISTA_A, "/rotas").lower())

    def test_nome_incorreto_nao_libera_acesso(self):
        registrar_motorista("Motorista A", CPF_A)
        _, _, resposta = identificar(MOTORISTA_A, "Nome Diferente", CPF_A)
        self.assertIn("não correspondem", resposta)
        with conectar() as conn:
            registro = conn.execute("SELECT papel,cpf_confirmado FROM usuarios WHERE telefone=?",
                                    (MOTORISTA_A,)).fetchone()
        self.assertEqual(registro["papel"], "cliente")
        self.assertFalse(registro["cpf_confirmado"])

    def test_vinculo_nao_pode_ser_reutilizado(self):
        registrar_motorista("Motorista A", CPF_A)
        identificar(MOTORISTA_A, "Motorista A", CPF_A)
        _, _, resposta = identificar(OUTRO, "Motorista A", CPF_A)
        self.assertIn("outro contato", resposta)
        with conectar() as conn:
            registro = conn.execute("SELECT papel FROM usuarios WHERE telefone=?", (OUTRO,)).fetchone()
        self.assertEqual(registro["papel"], "cliente")

    def test_admin_bloqueia_antes_e_depois_da_identificacao(self):
        resposta = registrar_motorista("Motorista A", CPF_A)
        self.assertIn("cadastrado", resposta.lower())
        bloqueio = receber_mensagem(ADMIN, "/motorista bloquear 1")
        self.assertIn("bloqueado", bloqueio.lower())
        _, _, tentativa = identificar(MOTORISTA_A, "Motorista A", CPF_A)
        self.assertIn("bloqueado", tentativa.lower())
        self.assertIn("reativado", receber_mensagem(ADMIN, "/motorista ativar 1").lower())
        self.assertIn("/rotas", receber_mensagem(MOTORISTA_A, CPF_A))
        self.assertIn("bloqueado", receber_mensagem(ADMIN, "/motorista bloquear 1").lower())
        self.assertIn("bloqueado", receber_mensagem(MOTORISTA_A, "/rotas").lower())

    def test_primeiro_motorista_aceita_a_rota(self):
        registrar_motorista("Motorista A", CPF_A)
        registrar_motorista("Motorista B", CPF_B)
        identificar(MOTORISTA_A, "Motorista A", CPF_A)
        identificar(MOTORISTA_B, "Motorista B", CPF_B)
        identificar(CLIENTE, "Maria Silva", CPF_CLIENTE)

        dia = (date.today() + timedelta(days=2)).strftime("%d/%m/%Y")
        for mensagem in ["/nova", "Sete Lagoas", "Belo Horizonte", dia,
                         "10:00", "-", "s"]:
            resultado = receber_mensagem(CLIENTE, mensagem)
        self.assertIn("cadastrada", resultado.lower())
        self.assertIn("atribuída", receber_mensagem(MOTORISTA_A, "/aceitar 1"))
        self.assertIn("indisponível", receber_mensagem(MOTORISTA_B, "/aceitar 1"))
        self.assertIn("Motorista A", receber_mensagem(ADMIN, "/motoristas"))
        with conectar() as conn:
            rota = conn.execute("SELECT status,motorista_id FROM rotas WHERE id=1").fetchone()
        self.assertEqual(rota["status"], "atribuida")
        self.assertEqual(rota["motorista_id"], 1)


if __name__ == "__main__":
    unittest.main()
