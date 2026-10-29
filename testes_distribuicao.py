"""Regras de reservas e capacidade; os testes concorrentes reais ficam em testes_postgres.py."""
import unittest
from unittest.mock import MagicMock

from distribuicao import RegistroIndisponivel, conferir_vaga, reservar_registro


class TestesDistribuicao(unittest.TestCase):
    def conexao(self, resultados):
        conexao = MagicMock()
        conexao.execute.return_value.fetchone.side_effect = resultados
        return conexao

    def test_reabrir_tela_reutiliza_reserva_ativa(self):
        conexao = self.conexao([("reserva-1", "GBR-000001", True, 0, False)])
        resposta = reservar_registro(conexao, "sessao-1", set())
        self.assertEqual(resposta["id_registro"], "GBR-000001")
        self.assertEqual(resposta["reserva_id"], "reserva-1")

    def test_esgotamento_na_sessao_nao_afirma_conclusao_global(self):
        conexao = self.conexao([None, None, (False,)])
        self.assertFalse(reservar_registro(conexao, "sessao-1", set())["concluido"])
        conexao = self.conexao([None, None, (True,)])
        self.assertTrue(reservar_registro(conexao, "sessao-1", set())["concluido"])

    def test_decima_resposta_cabe_e_decima_primeira_e_recusada(self):
        self.assertTrue(conferir_vaga(self.conexao([None, ("reserva",), (9, 0)]), "reserva", "sessao", "GBR-000001"))
        with self.assertRaises(RegistroIndisponivel):
            conferir_vaga(self.conexao([None, ("reserva",), (10, 0)]), "reserva", "sessao", "GBR-000001")

    def test_reserva_expirada_nao_toma_vaga_de_outros(self):
        with self.assertRaises(RegistroIndisponivel):
            conferir_vaga(self.conexao([None, ("reserva",), (9, 1)]), "reserva", "sessao", "GBR-000001")

    def test_reenvio_ja_salvo_nao_precisa_de_nova_vaga(self):
        self.assertFalse(conferir_vaga(self.conexao([("ja-salva",)]), "reserva", "sessao", "GBR-000001"))

    def test_sem_reserva_nao_insere_resposta(self):
        with self.assertRaises(RegistroIndisponivel):
            conferir_vaga(self.conexao([None, None]), "reserva", "sessao", "GBR-000001")


if __name__ == "__main__":
    unittest.main()
