"""Testes da aplicação de anotação, separados dos testes dos experimentos."""
import hashlib
import csv
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

from banco import exportar, salvar_anotacao
from categorias import validar_anotacao
from dados import sortear_registro


class TestesAnotacao(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.banco = Path(self.pasta.name) / "anotacoes.sqlite3"
        texto = "Confirme hoje. Você receberá um prêmio."
        self.registro = {"id_registro": "FWA-000001", "base_origem": "FRAUDWHATSAPP_BR",
                         "texto": texto, "sha256_texto": hashlib.sha256(texto.encode()).hexdigest()}

    def salvar(self, categorias=None, trecho="Confirme hoje.", nenhuma=False, nome="Pessoa de teste"):
        return salvar_anotacao("resposta-1", "sessao-1", nome, 25, "127.0.0.1", self.registro,
                               ["Urgência"] if categorias is None else categorias, trecho, nenhuma, self.banco)

    def test_trecho_obrigatorio_e_literal(self):
        for trecho in ("", "Trecho inventado"):
            with self.assertRaises(ValueError):
                self.salvar(trecho=trecho)
        self.assertFalse(self.banco.exists())

    def test_ausencia_explicita_nao_se_confunde_com_vazio(self):
        with self.assertRaises(ValueError):
            self.salvar(categorias=[])
        with self.assertRaises(ValueError):
            self.salvar(nenhuma=True)
        self.assertTrue(self.salvar(categorias=[], nenhuma=True))
        with closing(sqlite3.connect(self.banco)) as conexao:
            self.assertEqual(json.loads(conexao.execute("SELECT estrategias_identificadas FROM anotacoes").fetchone()[0]), [])

    def test_salva_metadados_sem_duplicar_envio(self):
        nome = "Nome com 'aspas'"
        self.assertTrue(self.salvar(nome=nome))
        self.assertFalse(self.salvar(nome=nome))
        with closing(sqlite3.connect(self.banco)) as conexao:
            linhas = conexao.execute("SELECT nome, idade, ip, data_hora_utc, evidencia_textual FROM anotacoes").fetchall()
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0][:3], (nome, 25, "127.0.0.1"))
        self.assertTrue(linhas[0][3].endswith("+00:00"))
        self.assertEqual(linhas[0][4], "Confirme hoje.")
        self.assertTrue(exportar(self.banco, bases={"WHATSAPP": [self.registro]}).exists())

    def test_mesmo_relato_recebe_varias_respostas_e_exporta_todas(self):
        self.salvar(nome="Wallace")
        salvar_anotacao("resposta-2", "sessao-2", "Vinicius", 25, None, self.registro,
                       ["Promessa de vantagem"], "Você receberá um prêmio.", caminho=self.banco)
        saida = exportar(self.banco, bases={"WHATSAPP": [self.registro]})
        with saida.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        self.assertEqual(len(linhas), 2)
        self.assertEqual({r["nome"] for r in linhas}, {"Wallace", "Vinicius"})
        self.assertTrue(all(r["texto_original"] == self.registro["texto"] for r in linhas))
        self.assertEqual({r["estrategias_identificadas"] for r in linhas}, {"Urgência", "Promessa de vantagem"})

    def test_varias_passagens_e_categorias(self):
        validar_anotacao(self.registro["texto"], ["Urgência", "Promessa de vantagem"],
                         "Confirme hoje.\nVocê receberá um prêmio.")

    def test_sorteio_respeita_vistos_e_esgotamento(self):
        outra = dict(self.registro, id_registro="GBR-000001", base_origem="GOLPEBR")
        bases = {"WHATSAPP": [self.registro], "GOLPEBR": [outra]}
        self.assertEqual(sortear_registro(bases, {self.registro["id_registro"]}), outra)
        self.assertIsNone(sortear_registro(bases, {self.registro["id_registro"], outra["id_registro"]}))

    @unittest.skipUnless(importlib.util.find_spec("streamlit"), "Instale Streamlit para testar a tela.")
    def test_formulario_preserva_texto_e_grava(self):
        from streamlit.testing.v1 import AppTest

        # Uma base pequena exercita o formulário sem rede nem respostas reais.
        import banco
        with patch.object(banco, "BANCO", self.banco), \
             patch("dados.carregar_bases", return_value={"WHATSAPP": [self.registro]}):
            tela = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=20).run()
            self.assertFalse(tela.exception)
            tela.text_input[0].input("Pessoa de teste")
            tela.number_input[0].set_value(25)
            tela.button[0].click().run()
            self.assertFalse(tela.exception)
            self.assertEqual(len(tela.checkbox), 9)
            self.assertEqual(tela.text_area[0].value, self.registro["texto"])
            tela.checkbox[0].check().run()
            self.assertEqual(tela.text_area[0].value, self.registro["texto"])
            tela.button[0].click().run()
            self.assertTrue(tela.error)
            self.assertFalse(self.banco.exists())
            tela.text_area[1].input("Confirme hoje.")
            tela.button[0].click().run()
            self.assertFalse(tela.exception)
            with closing(sqlite3.connect(self.banco)) as conexao:
                self.assertEqual(conexao.execute("SELECT COUNT(*) FROM anotacoes").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
