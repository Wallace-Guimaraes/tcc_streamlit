"""Fluxos da tela com exemplos fictícios e API simulada, sem banco ou rede."""
import hashlib
import importlib.util
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from categorias import CATEGORIAS
from consentimento import registrar_aceite


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Instale Streamlit para testar a tela.')
class TestesTela(unittest.TestCase):
    @contextmanager
    def abrir(self):
        from streamlit.testing.v1 import AppTest

        texto = 'ME CHAMO MARIA DA SILVA. Confirme hoje em t.me/exemplo ou nome.com@exemplo.org.'
        registro = dict(id_registro='GBR-000001', base_origem='GOLPEBR', texto=texto,
                        sha256_texto=hashlib.sha256(texto.encode()).hexdigest(), reserva_id=str(uuid4()))
        sessao = str(uuid4())
        with patch('cliente_api.sortear_pela_api', side_effect=[
                {'registro': registro, 'concluido': False}, {'registro': None, 'concluido': False}]) as sorteio, \
             patch('banco.salvar_anotacao', return_value=True) as salvar:
            tela = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=20)
            tela.session_state['participante'] = dict(nome='Pessoa de teste', email='pessoa@example.org')
            tela.session_state['consentimento'] = registrar_aceite('Pessoa de teste', 'pessoa@example.org', True)
            tela.session_state['sessao_id'] = sessao
            tela.session_state['vistos'] = set()
            tela.session_state['salvas'] = 0
            tela.run()
            self.assertFalse(tela.exception)
            yield tela, sorteio, salvar, registro

    def clicar(self, tela, rotulo):
        next(botao for botao in tela.button if botao.label == rotulo).click().run()
        self.assertFalse(tela.exception)

    def test_guia_oito_categorias_e_texto_mascarado(self):
        with self.abrir() as (tela, sorteio, salvar, registro):
            self.assertEqual(tela.expander[0].label, 'Como realizar a anotação')
            self.assertFalse(tela.expander[0].proto.expanded)
            guia = '\n'.join(item.value for item in tela.markdown)
            for categoria in CATEGORIAS:
                self.assertIn(categoria, guia)
            self.assertIn('fictícios', guia)
            self.assertIn('não significa que o registro não é fraude', guia)
            self.assertCountEqual([item.label for item in tela.checkbox], [*CATEGORIAS, 'Nenhuma das categorias'])
            self.assertEqual(tela.text_area[0].value,
                             'ME CHAMO [PESSOA]. Confirme hoje em [LINK] ou [EMAIL].')
            self.assertIn('MARIA DA SILVA', registro['texto'])
            sorteio.assert_called_once()
            salvar.assert_not_called()

    def test_falha_api_preserva_categorias_trecho_e_reserva(self):
        with self.abrir() as (tela, sorteio, salvar, registro):
            salvar.side_effect = ValueError('API indisponível')
            next(item for item in tela.checkbox if item.label == 'Urgência').check()
            next(item for item in tela.checkbox if item.label == 'Promessa de vantagem').check()
            tela.text_area[1].input('Confirme hoje')
            self.clicar(tela, 'Salvar e próximo')
            self.assertIn('API indisponível', tela.error[0].value)
            self.assertTrue(next(item for item in tela.checkbox if item.label == 'Urgência').value)
            self.assertTrue(next(item for item in tela.checkbox if item.label == 'Promessa de vantagem').value)
            self.assertEqual(tela.text_area[1].value, 'Confirme hoje')
            self.assertEqual(tela.session_state['anotacao_id'], registro['reserva_id'])
            self.assertEqual(tela.session_state['vistos'], set())
            self.assertEqual(tela.session_state['salvas'], 0)
            sorteio.assert_called_once()
            salvar.side_effect = None
            self.clicar(tela, 'Salvar e próximo')
            self.assertEqual(tela.session_state['salvas'], 1)
            self.assertEqual(salvar.call_count, 2)
            self.assertEqual(salvar.call_args.args[6:8], (['Urgência', 'Promessa de vantagem'], 'Confirme hoje'))

    def test_pular_nao_envia_anotacao_e_informa_registro_visto(self):
        with self.abrir() as (tela, sorteio, salvar, registro):
            tela.checkbox[0].check()
            tela.text_area[1].input('Confirme hoje')
            self.clicar(tela, 'Pular texto')
            salvar.assert_not_called()
            self.assertEqual(tela.session_state['salvas'], 0)
            self.assertEqual(sorteio.call_args.args[1], {registro['id_registro']})
            self.assertEqual(sorteio.call_count, 2)


if __name__ == '__main__':
    unittest.main()
