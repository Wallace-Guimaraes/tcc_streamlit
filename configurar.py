"""Cria senhas locais para o Docker sem alterar uma configuração existente."""
import secrets
from pathlib import Path


def configurar():
    caminho = Path(__file__).resolve().parent / ".env"
    if caminho.exists():
        print("O arquivo .env já existe e foi mantido.")
        return
    with caminho.open("x", encoding="utf-8") as arquivo:
        arquivo.write(f"POSTGRES_PASSWORD={secrets.token_hex(24)}\nCHAVE_API={secrets.token_urlsafe(32)}\n")
    print("Arquivo .env criado com senha do banco e chave da API. Não publique esse arquivo.")


if __name__ == "__main__":
    configurar()
