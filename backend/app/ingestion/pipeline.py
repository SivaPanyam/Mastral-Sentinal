import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.ingestion.processors import IncidentProcessor, LogProcessor, KnowledgeProcessor
import time

class IngestionPipeline:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db: Session = SessionLocal()
        
    def classify_file(self, filename: str) -> str:
        name_lower = filename.lower()
        if "incident" in name_lower and filename.endswith(".csv"):
            return "INCIDENT"
        elif "log" in name_lower and filename.endswith(".csv"):
            return "LOG"
        elif filename.endswith(('.md', '.txt', '.ipynb', '.pdf', '.docx')):
            return "KNOWLEDGE"
        else:
            return "UNKNOWN"

    def run(self):
        print(f"Starting ingestion pipeline on directory: {self.data_dir}")
        start_time = time.time()
        
        overall_stats = {
            "files_processed": 0,
            "incidents_added": 0,
            "logs_added": 0,
            "knowledge_added": 0,
            "errors": 0,
            "skipped": 0
        }
        
        if not os.path.exists(self.data_dir):
            print(f"Directory {self.data_dir} not found.")
            return

        incident_proc = IncidentProcessor(self.db)
        log_proc = LogProcessor(self.db)
        knowledge_proc = KnowledgeProcessor(self.db)

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if not os.path.isfile(file_path):
                continue
                
            file_type = self.classify_file(filename)
            print(f"Processing {filename} (Type: {file_type})...")
            
            stats = None
            if file_type == "INCIDENT":
                stats = incident_proc.process(file_path)
                if stats:
                    overall_stats["incidents_added"] += stats.get("inserted", 0)
            elif file_type == "LOG":
                stats = log_proc.process(file_path)
                if stats:
                    overall_stats["logs_added"] += stats.get("inserted", 0)
            elif file_type == "KNOWLEDGE":
                stats = knowledge_proc.process(file_path)
                if stats:
                    overall_stats["knowledge_added"] += stats.get("inserted", 0)
            else:
                print(f"Skipping unknown file type: {filename}")
                continue
                
            if stats:
                overall_stats["files_processed"] += 1
                overall_stats["errors"] += stats.get("errors", 0)
                overall_stats["skipped"] += stats.get("skipped", 0)
                
        duration = time.time() - start_time
        
        print("\n=== Ingestion Pipeline Final Report ===")
        print(f"Files Processed: {overall_stats['files_processed']}")
        print(f"Incidents Added: {overall_stats['incidents_added']}")
        print(f"Logs Added: {overall_stats['logs_added']}")
        print(f"Knowledge Documents Added: {overall_stats['knowledge_added']}")
        print(f"Duplicates Skipped: {overall_stats['skipped']}")
        print(f"Errors: {overall_stats['errors']}")
        print(f"Processing Time: {duration:.2f} seconds")
        print("=======================================")
        
        self.db.close()
