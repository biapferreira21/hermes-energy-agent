"""Corre o pipeline automaticamente de hora a hora.
Corre com: python scheduler.py
Para parar: Ctrl+C
"""
from apscheduler.schedulers.blocking import BlockingScheduler

from src.main import run_pipeline

scheduler = BlockingScheduler(timezone="Europe/Lisbon")


@scheduler.scheduled_job("interval", minutes=60)
def hourly_job() -> None:
    print("Hermes scheduler: a iniciar ciclo...")
    run_pipeline(max_per_feed=15)
    print("Hermes scheduler: ciclo concluido.")


if __name__ == "__main__":
    print("Hermes scheduler iniciado. Corre de hora a hora. Prima Ctrl+C para parar.")
    # Corre um ciclo imediatamente ao arrancar
    run_pipeline(max_per_feed=15)
    scheduler.start()
