from src.bootstrap.dependencies.ingestion import get_ingestion_pipeline

ingestion_pipeline = get_ingestion_pipeline()
ingestion_pipeline.run()