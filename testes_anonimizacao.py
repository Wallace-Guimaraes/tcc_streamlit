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

    def test_email_com_dominio_na_parte_local_e_links_curtos(self):
        original = 'Envie para nome.com@exemplo.org; veja t.me/exemplo ou bit.ly/oferta.'
        self.assertEqual(anonimizar_texto(original), 'Envie para [EMAIL]; veja [LINK] ou [LINK].')

    def test_dominio_sem_protocolo_oculta_consulta_e_fragmento(self):
        original = 'Veja exemplo.com.br?codigo=abc e exemplo.org#contato.'
        self.assertEqual(anonimizar_texto(original), 'Veja [LINK] e [LINK].')

    def test_apresentacoes_em_caixa_alta_baixa_e_com_dois_pontos(self):
        for apresentacao, nome in [('Meu nome é', 'maria da silva'),
                                   ('ME CHAMO', 'JOAO DA SILVA'),
                                   ('Meu nome é:', 'Maria da Silva'),
                                   ('Me chamo:', 'ana d’ávila'),
                                   ('Nome completo:\n', 'ÉRICA DE SOUZA')]:
            with self.subTest(apresentacao=apresentacao, nome=nome):
                original = f'{apresentacao} {nome}. {nome} pede ajuda.'
                esperado = f'{apresentacao} [PESSOA]. [PESSOA] pede ajuda.'
                self.assertEqual(anonimizar_texto(original), esperado)
                self.assertEqual(anonimizar_texto(nome, referencia=original), '[PESSOA]')
                self.assertEqual(anonimizar_texto(esperado), esperado)

    def test_nome_nao_oculta_instrucao_apos_apresentacao(self):
        for original, esperado in [
            ('Me chamo joao da silva e preciso que pague hoje.', 'Me chamo [PESSOA] e preciso que pague hoje.'),
            ('Me chamo Maria da Silva recebi uma oferta hoje.', 'Me chamo [PESSOA] recebi uma oferta hoje.'),
            ('ME CHAMO JOAO CONFIRME HOJE.', 'ME CHAMO [PESSOA] CONFIRME HOJE.'),
            ('Me chamo João e Maria. Confirme hoje.', 'Me chamo [PESSOA]. Confirme hoje.')]:
            with self.subTest(original=original):
                self.assertEqual(anonimizar_texto(original), esperado)

    def test_nao_promete_reconhecer_nome_sem_apresentacao(self):
        original = 'Maria da Silva recebeu um pedido do Banco Central.'
        self.assertEqual(anonimizar_texto(original), original)

    def test_nome_repetido_com_espacamento_normalizado_na_evidencia(self):
        referencia = 'Me chamo Maria  da Silva. Maria  da Silva pede ajuda.'
        for trecho in ('Maria da Silva', 'MARIA\tda Silva', 'Maria\nda Silva'):
            with self.subTest(trecho=trecho):
                validar_anotacao(anonimizar_texto(referencia), ['Vínculo emocional'], trecho,
                                 texto_original=referencia)
                self.assertEqual(anonimizar_texto(trecho, referencia=referencia), '[PESSOA]')

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
