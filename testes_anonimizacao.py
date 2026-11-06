"""Casos de regex e compatibilidade dos trechos com o texto apresentado."""
import unittest

from anonimizacao import anonimizar_texto
from categorias import validar_anotacao


class TestesAnonimizacao(unittest.TestCase):
    def test_email_links_e_pontuacao(self):
        original = 'Envie para maria.silva+teste@exemplo.com.br. Acesse https://exemplo.com/oferta?q=1, www.exemplo.org ou exemplo.net/oferta!'
        esperado = 'Envie para [EMAIL]. Acesse [LINK], [LINK] ou [LINK]!'
        self.assertEqual(anonimizar_texto(original), esperado)

    def test_nome_com_contexto_e_repeticao_no_trecho(self):
        original = 'Meu nome é Maria da Silva. Maria da Silva pede ajuda ao seu filho.'
        self.assertEqual(anonimizar_texto(original),
                         'Meu nome é [PESSOA]. [PESSOA] pede ajuda ao seu filho.')
        self.assertEqual(anonimizar_texto('Maria da Silva pede ajuda', referencia=original),
                         '[PESSOA] pede ajuda')

    def test_preserva_contexto_das_estrategias_e_marcadores(self):
        original = 'Banco Central. Seu filho precisa de ajuda. Meu nome é João. Confirme hoje!'
        esperado = 'Banco Central. Seu filho precisa de ajuda. Meu nome é [PESSOA]. Confirme hoje!'
        self.assertEqual(anonimizar_texto(original), esperado)
        self.assertEqual(anonimizar_texto(esperado), esperado)
        self.assertEqual(anonimizar_texto(''), '')

    def test_aceita_trechos_originais_e_tratados_sem_aceitar_identificador_inventado(self):
        original = 'Me chamo João da Silva. Escreva para joao@exemplo.org hoje.'
        tratado = anonimizar_texto(original)
        for trecho in (original, tratado, 'João da Silva.', '[PESSOA].'):
            validar_anotacao(tratado, ['Urgência'], trecho, texto_original=original)
        with self.assertRaises(ValueError):
            validar_anotacao(tratado, ['Urgência'], 'Escreva para inventado@exemplo.org hoje.',
                             texto_original=original)


if __name__ == '__main__':
    unittest.main()
