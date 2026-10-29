"""Integração opcional: use TEST_DATABASE_URL de um PostgreSQL exclusivo para testes.

Cria um schema temporário, sem ler nem alterar public.anotacoes.
"""
import asyncio
import hashlib
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Configure um PostgreSQL de testes em TEST_DATABASE_URL.")
class TestesPostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg import sql
        import api

        cls.api, cls.psycopg, cls.sql = api, psycopg, sql
        cls.endereco = os.environ["TEST_DATABASE_URL"]
        cls.schema = "teste_coleta_" + uuid4().hex
        with psycopg.connect(cls.endereco, connect_timeout=10) as conexao:
            conexao.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        cls.addClassCleanup(cls.remover_schema)
        cls.registros = {}
        for numero in range(3):
            identificador = f"GBR-{numero:06d}"
            texto = f"Confirme hoje o pedido {numero}."
            cls.registros[identificador] = {"id_registro": identificador, "base_origem": "GOLPEBR", "texto": texto,
                                           "sha256_texto": hashlib.sha256(texto.encode()).hexdigest()}
        cls.enterClassContext(patch.object(api, "conectar", side_effect=cls.conectar_teste))
        cls.enterClassContext(patch.object(api, "registros_por_id", return_value=cls.registros))
        cls.enterClassContext(patch.dict(os.environ, {"CHAVE_API": "teste-local"}))

        async def iniciar():
            async with api.iniciar(api.app):
                pass
        asyncio.run(iniciar())

    @classmethod
    def conectar_teste(cls):
        conexao = cls.psycopg.connect(cls.endereco, connect_timeout=10)
        conexao.execute(cls.sql.SQL("SET search_path TO {}").format(cls.sql.Identifier(cls.schema)))
        conexao.commit()
        conexao.isolation_level = cls.psycopg.IsolationLevel.READ_COMMITTED
        return conexao

    @classmethod
    def remover_schema(cls):
        if not cls.schema.startswith("teste_coleta_"):
            raise RuntimeError("Schema de teste inesperado.")
        with cls.psycopg.connect(cls.endereco, connect_timeout=10) as conexao:
            conexao.execute(cls.sql.SQL("DROP SCHEMA {} CASCADE").format(cls.sql.Identifier(cls.schema)))

    def setUp(self):
        from distribuicao import preparar_catalogo

        with self.conectar_teste() as conexao:
            self.assertEqual(conexao.execute("SELECT current_schema()").fetchone()[0], self.schema)
            conexao.execute("TRUNCATE reservas_coleta, anotacoes, registros_coleta")
            preparar_catalogo(conexao, self.registros)

    def anotacao(self, registro, sessao):
        from consentimento import registrar_aceite

        return self.api.Anotacao(id=registro["reserva_id"], sessao_id=sessao, nome="Pessoa de teste", email="pessoa@example.org",
                                id_registro=registro["id_registro"], sha256_texto=registro["sha256_texto"],
                                categorias=["Urgência"], trecho=registro["texto"],
                                **registrar_aceite("Pessoa de teste", "pessoa@example.org", True))

    def avaliar(self, _=None):
        sessao = str(uuid4())
        sorteado = self.api.sortear(self.api.PedidoSorteio(sessao_id=sessao))
        if sorteado["registro"] is None:
            return None
        anotacao = self.anotacao(sorteado["registro"], sessao)
        self.assertTrue(self.api.receber_anotacao(anotacao)["criada"])
        return anotacao

    def test_cobertura_limite_concorrente_e_reenvio(self):
        # Todos recebem uma resposta antes de um registro receber a segunda.
        for _ in range(3):
            self.avaliar()
        with self.conectar_teste() as conexao:
            contagens = conexao.execute("SELECT COUNT(*) FROM anotacoes GROUP BY id_registro").fetchall()
        self.assertEqual(sorted(linha[0] for linha in contagens), [1, 1, 1])

        # Mais participantes simultâneos do que as 27 vagas restantes.
        with ThreadPoolExecutor(max_workers=12) as executor:
            recebidas = list(executor.map(self.avaliar, range(45)))
        self.assertEqual(sum(a is not None for a in recebidas), 27)
        with self.conectar_teste() as conexao:
            contagens = conexao.execute("SELECT COUNT(*) FROM anotacoes GROUP BY id_registro").fetchall()
        self.assertEqual(sorted(linha[0] for linha in contagens), [10, 10, 10])
        ultima = next(a for a in recebidas if a is not None)
        self.assertFalse(self.api.receber_anotacao(ultima)["criada"])
        self.assertTrue(self.api.sortear(self.api.PedidoSorteio(sessao_id=uuid4()))["concluido"])

    def test_abandono_libera_vaga_e_resposta_atrasada_nao_excede_limite(self):
        from fastapi import HTTPException

        with self.conectar_teste() as conexao:
            conexao.execute("DELETE FROM registros_coleta WHERE id_registro<>%s", ("GBR-000000",))
        reservas = []
        for _ in range(10):
            sessao = str(uuid4())
            registro = self.api.sortear(self.api.PedidoSorteio(sessao_id=sessao))["registro"]
            reservas.append((sessao, registro))
        nova_sessao = str(uuid4())
        self.assertIsNone(self.api.sortear(self.api.PedidoSorteio(sessao_id=nova_sessao))["registro"])
        antiga_sessao, antiga = reservas[0]
        with self.conectar_teste() as conexao:
            conexao.execute("UPDATE reservas_coleta SET expira_em=CURRENT_TIMESTAMP-INTERVAL '1 minute' WHERE id=%s",
                            (antiga["reserva_id"],))
        self.assertIsNotNone(self.api.sortear(self.api.PedidoSorteio(sessao_id=nova_sessao))["registro"])
        with self.assertRaises(HTTPException) as erro:
            self.api.receber_anotacao(self.anotacao(antiga, antiga_sessao))
        self.assertEqual(erro.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
