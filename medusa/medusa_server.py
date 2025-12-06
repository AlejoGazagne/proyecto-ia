import os
import subprocess
import logging
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Medusa Fuzzing Service")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s medusa_service - %(message)s"
)
logger = logging.getLogger(__name__)

class AnalysisRequest(BaseModel):
    analysis_id: str
    filename: str

WORKSPACE_DIR = "/workspace"


def log_command_output(command: str, result: subprocess.CompletedProcess) -> None:
    """Log Medusa execution details for visibility."""
    logger.info("Command: %s", command)
    logger.info("Exit code: %s", result.returncode)
    stdout = result.stdout if result.stdout else "<empty>"
    stderr = result.stderr if result.stderr else "<empty>"
    logger.info("STDOUT:\n%s", stdout)
    logger.info("STDERR:\n%s", stderr)

@app.post("/analyze")
async def analyze(request: AnalysisRequest = Body(...)):
    """
    Analiza un contrato con Medusa (fuzzer).
    """
    contract_path = os.path.join(WORKSPACE_DIR, request.analysis_id, request.filename)
    
    if not os.path.exists(contract_path):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": f"Contract not found: {contract_path}",
                "error_type": "file_not_found"
            }
        )
    
    try:
        # Ejecutar Medusa
        command = (
            f"medusa fuzz --compilation-target {contract_path} --test-limit 1000 --no-color"
        )
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(contract_path)
        )
        log_command_output(command, result)
        
        is_success = (result.returncode == 0)
        error_type = None
        
        if not is_success:
            stderr_lower = result.stderr.lower()
            if "compilation failed" in stderr_lower:
                error_type = "compilation_error"
            elif "not found" in stderr_lower:
                error_type = "tool_not_found"
            else:
                error_type = "analysis_error"
        
        return {
            "success": is_success,
            "command": f"medusa fuzz --compilation-target {contract_path} --test-limit 1000",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "error_type": error_type
        }
        
    except subprocess.TimeoutExpired:
        logger.exception("Medusa analysis timed out for %s", contract_path)
        return {
            "success": False,
            "error": "Analysis timed out",
            "error_type": "timeout"
        }
    except Exception as e:
        logger.exception("Unexpected Medusa error for %s", contract_path)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unexpected_error"
        }

@app.get("/")
async def root():
    return {"service": "Medusa Fuzzing", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
