"""Cobertura e privacidade da consulta administrativa, com conexão simulada."""
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

import psycopg

from relatorio_coleta import CONSULTA, consultar_cobertura, formatar_relatorio, main


class TestesRelatorio(unittest.TestCase):
    def consultar(self, linhas):
        conexao = MagicMock()
        conexao.__enter__.return_value = conexao
        conexao.execute.return_value.fetchall.return_value = linhas
        with patch('relatorio_coleta.psycopg.connect', return_value=conexao):
            relatorio = consultar_cobertura('conexao-ficticia')
        self.assertTrue(conexao.read_only)
        conexao.execute.assert_called_once_with(CONSULTA)
        return relatorio

    def test_faixas_zero_respostas_e_totais_fecham(self):
        relatorio = self.consultar([
            ('GOLPEBR', 3, 1, 1, 1, 2, 11, 20, 0),
            ('FRAUDWHATSAPP_BR', 2, 1, 1, 0, 1, 9, 20, 0),
            (None, 5, 2, 2, 1, 3, 20, 20, 1)])
        self.assertEqual(relatorio['total'], dict(registros=5, sem_respostas=2, uma_a_nove=2,
                                                dez_ou_mais=1, com_respostas=3, respostas=20))
        for campo, valor in relatorio['total'].items():
            self.assertEqual(valor, sum(base[campo] for base in relatorio['por_base']))
        self.assertEqual(relatorio['respostas_fora_catalogo'], 0)
        texto = formatar_relatorio(relatorio)
        self.assertIn('TOTAL | 5 | 2 | 2 | 1 | 3 | 20', texto)
        self.assertIn('não são pessoas participantes', texto)
        self.assertIn('Gerado em UTC:', texto)

    def test_catalogo_vazio_e_respostas_historicas(self):
        for respostas in (0, 2):
            with self.subTest(respostas=respostas):
                relatorio = self.consultar([(None, 0, 0, 0, 0, 0, 0, respostas, 1)])
                self.assertEqual(relatorio['por_base'], [])
                self.assertEqual(relatorio['total']['registros'], 0)
                self.assertEqual(relatorio['respostas_gravadas'], respostas)
                self.assertEqual(relatorio['respostas_fora_catalogo'], respostas)

    def test_consulta_inclui_catalogo_e_nao_le_dados_pessoais(self):
        sql = CONSULTA.lower()
        self.assertIn('left join respostas', sql)
        self.assertIn('registros_coleta', sql)
        for proibido in ('nome', 'email', 'sessao_id', 'evidencia_textual', 'estrategias_identificadas',
                         'insert', 'update', 'delete', 'create', 'alter'):
            self.assertNotIn(proibido, sql)

    def test_erros_nao_expoem_credenciais_ou_traceback(self):
        segredo = 'postgresql://pesquisador:senha@servidor/banco'
        for erro in (psycopg.OperationalError(segredo), ValueError(segredo)):
            saida, erros = io.StringIO(), io.StringIO()
            with patch.dict(os.environ, {'DATABASE_URL': segredo}), \
                 patch('relatorio_coleta.psycopg.connect', side_effect=erro), \
                 redirect_stdout(saida), redirect_stderr(erros):
                self.assertEqual(main(), 1)
            self.assertEqual(saida.getvalue(), '')
            self.assertNotIn(segredo, erros.getvalue())
            self.assertNotIn('Traceback', erros.getvalue())

    def test_sem_configuracao_nao_abre_conexao(self):
        with patch.dict(os.environ, {'DATABASE_URL': ''}), \
             patch('relatorio_coleta.psycopg.connect') as conectar, redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 1)
        conectar.assert_not_called()


if __name__ == '__main__':
    unittest.main()
