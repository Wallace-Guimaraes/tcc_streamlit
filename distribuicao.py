"""Distribuição centralizada e limite de respostas, dentro de transações PostgreSQL."""
from uuid import uuid4

LIMITE_RESPOSTAS = 10
RESERVA_MINUTOS = 30
TRAVA_COLETA = 2026102901


class RegistroIndisponivel(ValueError):
    pass


def bloquear_coleta(conexao):
    # A mesma trava protege sorteio e gravação em todos os processos da API.
    conexao.execute("SELECT pg_advisory_xact_lock(%s)", (TRAVA_COLETA,))


def preparar_catalogo(conexao, registros):
    conexao.execute("""CREATE TABLE IF NOT EXISTS registros_coleta (
        id_registro TEXT PRIMARY KEY, base_origem TEXT NOT NULL, sha256_texto TEXT NOT NULL
    )""")
    conexao.execute("""CREATE TABLE IF NOT EXISTS reservas_coleta (
        id UUID PRIMARY KEY, sessao_id TEXT UNIQUE NOT NULL,
        id_registro TEXT NOT NULL REFERENCES registros_coleta(id_registro),
        expira_em TIMESTAMPTZ NOT NULL
    )""")
    conexao.execute("CREATE INDEX IF NOT EXISTS anotacoes_por_registro ON anotacoes (id_registro)")
    conexao.execute("CREATE INDEX IF NOT EXISTS reservas_por_registro ON reservas_coleta (id_registro, expira_em)")
    with conexao.cursor() as cursor:
        cursor.executemany("""INSERT INTO registros_coleta (id_registro, base_origem, sha256_texto)
            VALUES (%s,%s,%s) ON CONFLICT (id_registro) DO NOTHING""",
            [(r["id_registro"], r["base_origem"], r["sha256_texto"]) for r in registros.values()])


def reservar_registro(conexao, sessao_id, vistos):
    bloquear_coleta(conexao)
    atual = conexao.execute("""SELECT r.id, r.id_registro, r.expira_em > CURRENT_TIMESTAMP,
        (SELECT COUNT(*) FROM anotacoes a WHERE a.id_registro=r.id_registro),
        EXISTS (SELECT 1 FROM anotacoes a WHERE a.sessao_id=r.sessao_id AND a.id_registro=r.id_registro)
        FROM reservas_coleta r WHERE r.sessao_id=%s""", (sessao_id,)).fetchone()
    if atual and atual[2] and atual[3] < LIMITE_RESPOSTAS and not atual[4] and atual[1] not in vistos:
        return {"id_registro": atual[1], "reserva_id": str(atual[0]), "concluido": False}

    # Trocar/pular libera a reserva anterior da própria sessão.
    conexao.execute("DELETE FROM reservas_coleta WHERE sessao_id=%s", (sessao_id,))
    candidato = conexao.execute("""WITH respostas AS (
            SELECT id_registro, COUNT(*) AS quantidade FROM anotacoes GROUP BY id_registro
        ), reservas AS (
            SELECT id_registro, COUNT(*) AS quantidade FROM reservas_coleta
            WHERE expira_em > CURRENT_TIMESTAMP GROUP BY id_registro
        )
        SELECT r.id_registro
        FROM registros_coleta r
        LEFT JOIN respostas a USING (id_registro)
        LEFT JOIN reservas v USING (id_registro)
        WHERE COALESCE(a.quantidade,0) + COALESCE(v.quantidade,0) < %s
          AND NOT (r.id_registro = ANY(%s::text[]))
          AND NOT EXISTS (SELECT 1 FROM anotacoes propria
              WHERE propria.sessao_id=%s AND propria.id_registro=r.id_registro)
        ORDER BY COALESCE(a.quantidade,0) + COALESCE(v.quantidade,0),
                 COALESCE(a.quantidade,0), random()
        LIMIT 1""", (LIMITE_RESPOSTAS, list(vistos), sessao_id)).fetchone()
    if candidato is None:
        concluido = conexao.execute("""SELECT NOT EXISTS (
            SELECT r.id_registro FROM registros_coleta r
            LEFT JOIN anotacoes a USING (id_registro)
            GROUP BY r.id_registro HAVING COUNT(a.id) < %s
        )""", (LIMITE_RESPOSTAS,)).fetchone()[0]
        return {"id_registro": None, "reserva_id": None, "concluido": concluido}
    reserva_id = str(uuid4())
    conexao.execute("""INSERT INTO reservas_coleta (id,sessao_id,id_registro,expira_em)
        VALUES (%s,%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'))""",
        (reserva_id, sessao_id, candidato[0], RESERVA_MINUTOS))
    return {"id_registro": candidato[0], "reserva_id": reserva_id, "concluido": False}


def conferir_vaga(conexao, anotacao_id, sessao_id, id_registro):
    """Mantém a trava até a transação que grava a anotação terminar."""
    bloquear_coleta(conexao)
    existente = conexao.execute("""SELECT id FROM anotacoes
        WHERE id=%s OR (sessao_id=%s AND id_registro=%s) LIMIT 1""",
        (anotacao_id, sessao_id, id_registro)).fetchone()
    if existente:
        return False  # Reenvio de resposta já salva, mesmo se ela completou a décima vaga.
    reserva = conexao.execute("""SELECT id FROM reservas_coleta
        WHERE id=%s AND sessao_id=%s AND id_registro=%s""",
        (anotacao_id, sessao_id, id_registro)).fetchone()
    if not reserva:
        raise RegistroIndisponivel("Esta reserva foi trocada ou não existe. Use Pular texto para receber um novo registro.")
    respostas, outras_reservas = conexao.execute("""SELECT
        (SELECT COUNT(*) FROM anotacoes WHERE id_registro=%s),
        (SELECT COUNT(*) FROM reservas_coleta WHERE id_registro=%s
            AND sessao_id<>%s AND expira_em > CURRENT_TIMESTAMP)""",
        (id_registro, id_registro, sessao_id)).fetchone()
    if respostas >= LIMITE_RESPOSTAS:
        raise RegistroIndisponivel("Este registro já atingiu dez respostas. Use Pular texto para continuar.")
    if respostas + outras_reservas >= LIMITE_RESPOSTAS:
        raise RegistroIndisponivel("A reserva expirou e as vagas estão ocupadas. Tente salvar mais tarde ou use Pular texto.")
    return True


def liberar_reserva(conexao, sessao_id, reserva_id):
    conexao.execute("DELETE FROM reservas_coleta WHERE sessao_id=%s AND id=%s", (sessao_id, reserva_id))
