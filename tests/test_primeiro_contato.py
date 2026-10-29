"""Testes locais do atendimento inicial e das permissões.

Executar: python -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

from banco import conectar, criar_admin_local, preparar_banco, selecionar_banco
from mensagens import receber_mensagem


CLIENTE = "5500000000003"
ADMIN = "5500000000001"
MOTORISTA = "5500000000002"


class BoasVindasTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="teste_rotas_")
        selecionar_banco(Path(self.pasta.name) / "testes.db")
        preparar_banco()
        criar_admin_local(ADMIN)

    def tearDown(self):
        self.pasta.cleanup()

    def test_nome_obrigatorio_antes_do_menu(self):
        primeiro = receber_mensagem(CLIENTE, "oi")
        self.assertIn("como posso chamar", primeiro.lower())
        self.assertNotIn("/nova", primeiro)

        invalido = receber_mensagem(CLIENTE, "/nova")
        self.assertIn("nome", invalido.lower())

        invalido = receber_mensagem(CLIENTE, "12345")
        self.assertIn("nome", invalido.lower())

        menu = receber_mensagem(CLIENTE, "Maria Silva")
        self.assertIn("Maria Silva", menu)
        self.assertIn("/nova", menu)
        with conectar() as conn:
            usuario = conn.execute(
                "SELECT nome, nome_confirmado FROM usuarios WHERE telefone=?", (CLIENTE,)
            ).fetchone()
        self.assertEqual(usuario["nome"], "Maria Silva")
        self.assertEqual(usuario["nome_confirmado"], 1)

        rota = receber_mensagem(CLIENTE, "/nova")
        self.assertIn("origem", rota.lower())

    def test_nome_persiste_sem_perguntar_novamente(self):
        receber_mensagem(CLIENTE, "oi")
        receber_mensagem(CLIENTE, "João")
        retorno = receber_mensagem(CLIENTE, "/ajuda")
        self.assertIn("João", retorno)
        self.assertIn("/nova", retorno)
        self.assertNotIn("como posso chamar", retorno.lower())

    def test_motoristas_e_administrador_nao_precisam_cadastrar_nome(self):
        registro = receber_mensagem(
            ADMIN, f"/motorista adicionar {MOTORISTA} Motorista A"
        )
        self.assertIn("cadastrado", registro.lower())
        texto_admin = receber_mensagem(ADMIN, "/resumo")
        self.assertNotIn("como posso chamar", texto_admin.lower())
        texto_motorista = receber_mensagem(MOTORISTA, "/rotas")
        self.assertNotIn("como posso chamar", texto_motorista.lower())


if __name__ == "__main__":
    unittest.main()
