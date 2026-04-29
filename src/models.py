from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func

from src.db import Base


class ResearchItem(Base):
    __tablename__ = "research_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    source = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

    raw_text = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # Classificacao
    asset_classes = Column(Text, default="[]")
    instruments = Column(Text, default="[]")
    companies = Column(Text, default="[]")
    institutions = Column(Text, default="[]")
    regions = Column(Text, default="[]")
    market_layer = Column(String, nullable=True)

    # Blockchain / tokenizacao
    blockchain_relation = Column(String, nullable=True)
    tokenization = Column(Boolean, default=False)
    tokenized_asset = Column(String, nullable=True)
    stablecoin_relation = Column(Boolean, default=False)
    stablecoin_or_digital_money = Column(String, nullable=True)
    adoption_stage = Column(String, nullable=True)

    # Scores e relevancia
    financial_relevance = Column(String, nullable=True)
    research_relevance = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    signal_score = Column(Float, nullable=True)

    # Sinais de investimento (adicionados na v2)
    price_driver = Column(String, nullable=True)      # supply/demand/geopolitical/regulatory/financial/corporate/none
    market_sentiment = Column(String, nullable=True)  # bullish/bearish/neutral/mixed/unclear
    time_horizon = Column(String, nullable=True)      # immediate/short_term/medium_term/long_term/unclear

    # JSON completo da classificacao
    classification_json = Column(Text, nullable=True)
