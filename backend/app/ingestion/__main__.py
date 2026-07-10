import argparse
import os
from app.ingestion.pipeline import IngestionPipeline

def main():
    parser = argparse.ArgumentParser(description="Mastra Sentinel Data Ingestion Pipeline")
    parser.add_argument("--data-dir", type=str, default=os.path.join(os.getcwd(), "data"), help="Directory containing dataset files")
    
    args = parser.parse_args()
    
    pipeline = IngestionPipeline(data_dir=args.data_dir)
    pipeline.run()

if __name__ == "__main__":
    main()
