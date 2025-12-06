import os
import subprocess
import json
import logging
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Solc Compilation Service")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s solc_service - %(message)s"
)
logger = logging.getLogger(__name__)

class AnalysisRequest(BaseModel):
    analysis_id: str
    filename: str

WORKSPACE_DIR = "/workspace"


def log_command_output(command: str, result: subprocess.CompletedProcess) -> None:
    """Log complete Solc command output for troubleshooting."""
    logger.info("Command: %s", command)
    logger.info("Exit code: %s", result.returncode)
    stdout = result.stdout if result.stdout else "<empty>"
    stderr = result.stderr if result.stderr else "<empty>"
    logger.info("STDOUT:\n%s", stdout)
    logger.info("STDERR:\n%s", stderr)

@app.post("/analyze")
async def analyze(request: AnalysisRequest = Body(...)):
    """
    Compila un contrato con Solc.
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
        # Ejecutar Solc
        command = ["solc", "--combined-json", "abi,bin,ast", contract_path]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )
        log_command_output(" ".join(command), result)
        
        is_success = (result.returncode == 0)
        error_type = None
        compiled_json = None
        
        if is_success:
            # Intentar parsear la salida JSON
            try:
                compiled_json = json.loads(result.stdout)
            except:
                compiled_json = {"raw": result.stdout}
        else:
            stderr_lower = result.stderr.lower()
            if "compilation failed" in stderr_lower or "error" in stderr_lower:
                error_type = "compilation_error"
            elif "not found" in stderr_lower:
                error_type = "tool_not_found"
            else:
                error_type = "compilation_error"
        
        return {
            "success": is_success,
            "command": f"solc --combined-json abi,bin,ast {contract_path}",
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "error_type": error_type
        }
        
    except subprocess.TimeoutExpired:
        logger.exception("Solc analysis timed out for %s", contract_path)
        return {
            "success": False,
            "error": "Compilation timed out",
            "error_type": "timeout"
        }
    except Exception as e:
        logger.exception("Unexpected Solc error for %s", contract_path)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unexpected_error"
        }

@app.get("/")
async def root():
    return {"service": "Solc Compiler", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
