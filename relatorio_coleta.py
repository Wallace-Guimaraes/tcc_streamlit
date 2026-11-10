"""Consulta administrativa agregada, sem importar a API ou inicializar tabelas."""
import os
import sys
from datetime import datetime, timezone

import psycopg


# Um único SELECT fornece o mesmo retrato para totais e faixas por base.
# Não lê identificação de participantes, sessões, estratégias ou evidências.
CONSULTA = """WITH respostas AS (
    SELECT id_registro, COUNT(*) AS quantidade
    FROM anotacoes GROUP BY id_registro
), cobertura AS (
    SELECT r.base_origem, COALESCE(a.quantidade, 0) AS quantidade
    FROM registros_coleta r LEFT JOIN respostas a USING (id_registro)
)
SELECT base_origem, COUNT(*) AS registros,
       COUNT(*) FILTER (WHERE quantidade = 0) AS sem_respostas,
       COUNT(*) FILTER (WHERE quantidade BETWEEN 1 AND 9) AS uma_a_nove,
       COUNT(*) FILTER (WHERE quantidade >= 10) AS dez_ou_mais,
       COUNT(*) FILTER (WHERE quantidade > 0) AS com_respostas,
       COALESCE(SUM(quantidade), 0) AS respostas,
       (SELECT COUNT(*) FROM anotacoes) AS respostas_gravadas,
       GROUPING(base_origem) AS total_geral
FROM cobertura GROUP BY GROUPING SETS ((base_origem), ())
ORDER BY GROUPING(base_origem), base_origem"""

CAMPOS = ("registros", "sem_respostas", "uma_a_nove", "dez_ou_mais", "com_respostas", "respostas")


def consultar_cobertura(endereco):
    # O modo somente leitura é definido antes do início da transação.
    # Não usa api.conectar/iniciar: nenhum DDL ou migração é executado.
    with psycopg.connect(endereco, connect_timeout=10) as conexao:
        conexao.read_only = True
        linhas = conexao.execute(CONSULTA).fetchall()
    por_base = [dict(base_origem=linha[0], **dict(zip(CAMPOS, map(int, linha[1:7]))))
                for linha in linhas if not linha[8]]
    geral = next(linha for linha in linhas if linha[8])
    total = dict(zip(CAMPOS, map(int, geral[1:7])))
    respostas_gravadas = int(geral[7])
    return {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "por_base": por_base, "total": total, "respostas_gravadas": respostas_gravadas,
            "respostas_fora_catalogo": respostas_gravadas - total["respostas"]}


def formatar_relatorio(relatorio):
    linhas = ["Cobertura da coleta — retrato pontual", f"Gerado em UTC: {relatorio['gerado_em_utc']}",
              "Base | Registros | 0 respostas | 1–9 | 10 ou mais | Com respostas | Respostas no catálogo"]
    for base in [*relatorio["por_base"], dict(base_origem="TOTAL", **relatorio["total"])]:
        linhas.append(" | ".join([base["base_origem"], *(str(base[campo]) for campo in CAMPOS)]))
    linhas.extend([f"Respostas efetivamente gravadas: {relatorio['respostas_gravadas']}",
                   f"Respostas sem registro no catálogo: {relatorio['respostas_fora_catalogo']}",
                   "Reservas não são respostas. Registros com respostas não são pessoas participantes.",
                   "Pessoas distintas não são contabilizadas: sessões não comprovam identidade individual.",
                   "Cobertura não demonstra concordância, consenso ou validação científica dos rótulos."])
    return "\n".join(linhas)


def main():
    endereco = os.environ.get("DATABASE_URL", "").strip()
    if not endereco:
        print("Configure DATABASE_URL no ambiente restrito do pesquisador.", file=sys.stderr)
        return 1
    try:
        relatorio = consultar_cobertura(endereco)
    except (psycopg.Error, ValueError):
        print("Não foi possível consultar o PostgreSQL. Confira a conexão e as permissões de leitura.", file=sys.stderr)
        return 1
    print(formatar_relatorio(relatorio))
    return 0


if __name__ == "__main__":
    sys.exit(main())
