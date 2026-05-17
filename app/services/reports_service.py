import os
import json
from fastapi import HTTPException

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB safety limit

class ReportsService:
    @staticmethod
    def read_and_validate_report(file_path: str) -> dict:
        """Safely validates, bounds file size, and parses JSON/SARIF documents from reports/."""
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Report file {os.path.basename(file_path)} not found.")
        
        # Safety Check: Limit memory utilization
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail=f"Report file {os.path.basename(file_path)} exceeds 5MB size limit.")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Report file {os.path.basename(file_path)} contains malformed JSON.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read report: {str(e)}")
