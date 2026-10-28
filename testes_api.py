"""Testes HTTP da API com a conexão PostgreSQL substituída por um objeto de teste."""
import hashlib
import importlib.util
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4


@unittest.skipUnless(all(importlib.util.find_spec(n) for n in ("fastapi", "psycopg", "httpx")), "Instale requirements_api.txt e httpx.")
class TestesAPI(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        import api

        self.api = api
        texto = "Confirme hoje."
        self.registro = {"id_registro": "FWA-000001", "base_origem": "FRAUDWHATSAPP_BR", "texto": texto,
                         "sha256_texto": hashlib.sha256(texto.encode()).hexdigest()}
        self.conexao = MagicMock()
        self.conexao.__enter__.return_value = self.conexao
        self.conexao.execute.return_value.fetchone.return_value = ("salva",)
        for contexto in (patch.dict(os.environ, {"CHAVE_API": "chave-de-teste"}),
                         patch.object(api, "conectar", return_value=self.conexao),
                         patch.object(api, "registros_por_id", return_value={"FWA-000001": self.registro})):
            contexto.start()
            self.addCleanup(contexto.stop)
        self.cliente = TestClient(api.app)
        self.dados = {"id": str(uuid4()), "sessao_id": str(uuid4()), "nome": "Pessoa de teste", "idade": 25,
                      "ip": None, "id_registro": "FWA-000001", "sha256_texto": self.registro["sha256_texto"],
                      "categorias": ["Urgência"], "trecho": texto, "nenhuma": False}

    def enviar(self, dados=None):
        return self.cliente.post("/anotacoes", json=self.dados if dados is None else dados,
                                 headers={"X-API-Key": "chave-de-teste"})

    def test_recusa_envio_sem_chave(self):
        resposta = self.cliente.post("/anotacoes", json=self.dados)
        self.assertEqual(resposta.status_code, 401)
        self.conexao.execute.assert_not_called()

    def test_grava_apenas_apos_validar_texto_e_categoria(self):
        resposta = self.enviar()
        self.assertEqual(resposta.json(), {"criada": True})
        parametros = self.conexao.execute.call_args.args[1]
        self.assertEqual(parametros[6], "FRAUDWHATSAPP_BR")
        self.assertEqual(json.loads(parametros[8]), ["Urgência"])
        self.assertEqual(self.enviar(dict(self.dados, trecho="Passagem inventada")).status_code, 422)
        self.assertEqual(self.enviar(dict(self.dados, sha256_texto="0"*64)).status_code, 422)

    def test_nenhuma_aceita_trecho_vazio_e_vazio_sem_decisao_e_recusado(self):
        self.assertEqual(self.enviar(dict(self.dados, categorias=[], trecho="", nenhuma=True)).status_code, 200)
        self.assertEqual(self.enviar(dict(self.dados, categorias=[], trecho="", nenhuma=False)).status_code, 422)

    def test_reenvio_retorna_sem_criar_copia(self):
        self.conexao.execute.return_value.fetchone.return_value = None
        self.assertEqual(self.enviar().json(), {"criada": False})

    def test_falha_no_postgres_nao_e_confirmada_como_gravacao(self):
        self.conexao.execute.side_effect = self.api.psycopg.OperationalError("indisponível")
        self.assertEqual(self.enviar().status_code, 503)

    def test_saude_confere_banco(self):
        self.assertEqual(self.cliente.get("/saude").json(), {"status": "ok"})


class TestesCliente(unittest.TestCase):
    def test_sem_url_nao_grava_em_sqlite_alternativo(self):
        from banco import salvar_anotacao
        registro = {"texto": "Confirme hoje.", "id_registro": "FWA-000001", "sha256_texto": "0" * 64}
        with patch.dict(os.environ, {"URL_API": ""}), patch("banco.conectar") as conectar:
            with self.assertRaisesRegex(ValueError, "URL_API"):
                salvar_anotacao(str(uuid4()), str(uuid4()), "Pessoa", 25, None, registro, ["Urgência"], "Confirme hoje.")
            conectar.assert_not_called()

    def test_erro_de_rede_nao_grava_em_sqlite_alternativo(self):
        from banco import salvar_anotacao
        registro = {"texto": "Confirme hoje.", "id_registro": "FWA-000001", "sha256_texto": "0" * 64}
        with patch.dict(os.environ, {"URL_API": "https://api.example", "CHAVE_API": "teste"}), \
             patch("cliente_api.urllib.request.urlopen", side_effect=OSError("sem rede")), patch("banco.conectar") as conectar:
            with self.assertRaises(ValueError):
                salvar_anotacao(str(uuid4()), str(uuid4()), "Pessoa", 25, None, registro, ["Urgência"], "Confirme hoje.")
            conectar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
