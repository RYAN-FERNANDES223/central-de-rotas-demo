"""Confere a preparação de dados fictícios usada pelo site Streamlit."""
import tempfile
import unittest
from pathlib import Path

from banco import conectar, selecionar_banco
from demo_data import PERFIS, CPFS_TESTE, enviar, preparar_cenario


class DemonstraçãoSmokeTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="rotas_demo_")
        selecionar_banco(Path(self.pasta.name) / "demo.db")

    def tearDown(self):
        self.pasta.cleanup()

    def test_cenario_motoristas_precisam_identificar(self):
        preparar_cenario()
        with conectar() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM motoristas WHERE cpf_hash IS NOT NULL").fetchone()[0], 2)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM rotas").fetchone()[0], 2)
            for nome in ("Motorista A", "Motorista B"):
                self.assertIsNone(conn.execute(
                    "SELECT papel FROM usuarios WHERE telefone=?", (PERFIS[nome],)
                ).fetchone())

        self.assertIn("nome", enviar("Motorista A", "oi").lower())
        self.assertIn("cpf", enviar("Motorista A", "Motorista A").lower())
        self.assertIn("/rotas", enviar("Motorista A", CPFS_TESTE["Motorista A"]))
        self.assertIn("Rotas disponíveis", enviar("Motorista A", "/rotas"))

        self.assertIn("nome", enviar("Cliente", "oi").lower())
        self.assertIn("cpf", enviar("Cliente", "Maria Silva").lower())
        self.assertIn("/nova", enviar("Cliente", CPFS_TESTE["Cliente visitante"]))


if __name__ == "__main__":
    unittest.main()
