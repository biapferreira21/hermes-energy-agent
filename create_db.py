"""Cria a base de dados SQLite com todas as tabelas.
Corre UMA VEZ antes de usar o agente pela primeira vez.
Corre com: python create_db.py
"""
from src.db import init_db

if __name__ == "__main__":
    init_db()
    print("Base de dados Hermes criada com sucesso!")
    print("Ficheiro: data/hermes_energy.db")
