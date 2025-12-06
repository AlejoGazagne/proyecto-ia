import os
import subprocess
import json
import logging
from typing import Optional
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s slither_service - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Slither Analysis Service")

class AnalysisRequest(BaseModel):
    analysis_id: str
    filename: str

WORKSPACE_DIR = "/workspace"


def summarize_detectors(generated_json: Optional[dict]) -> list:
    """Return reduced detector info required by the API/logs."""
    detectors_summary = []
    if not isinstance(generated_json, dict):
        return detectors_summary
    try:
        raw_detectors = generated_json.get("results", {}).get("detectors", [])
        for detector in raw_detectors:
            detectors_summary.append(
                {
                    "check": detector.get("check"),
                    "impact": detector.get("impact"),
                    "confidence": detector.get("confidence"),
                    "description": detector.get("description"),
                    "id": detector.get("id"),
                }
            )
    except Exception as exc:
        logger.exception("Error summarizing Slither detectors: %s", exc)
    return detectors_summary


def log_command_output(command: str, result: subprocess.CompletedProcess) -> None:
    """Log command execution details for observability."""
    logger.info("Command: %s", command)
    logger.info("Exit code: %s", result.returncode)
    stdout = result.stdout if result.stdout else "<empty>"
    stderr = result.stderr if result.stderr else "<empty>"
    logger.info("STDOUT:\n%s", stdout)
    logger.info("STDERR:\n%s", stderr)

def classify_error(result):
    """
    Clasifica el tipo de error de Slither.
    """
    stderr_lower = result.stderr.lower()
    
    if "compilation failed" in stderr_lower or "compilation error" in stderr_lower:
        return "compilation_error"
    elif "syntax error" in stderr_lower:
        return "syntax_error"
    elif result.returncode <= 255 and result.returncode > 0:
        # Para Slither, exit codes 1-255 indican vulnerabilidades encontradas
        return "vulnerabilities_found"
    else:
        return "unknown_error"

@app.post("/analyze")
async def analyze(request: AnalysisRequest = Body(...)):
    """
    Analiza un contrato con Slither.
    """
    contract_path = os.path.join(WORKSPACE_DIR, request.analysis_id, request.filename)
    output_json = os.path.join(WORKSPACE_DIR, request.analysis_id, "slither-report.json")
    
    if not os.path.exists(contract_path):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": f"Contract not found: {contract_path}",
                "error_type": "file_not_found"
            }
        )

    command_str = f"slither {contract_path} --json {output_json}"
    try:
        command = ["slither", contract_path, "--json", output_json]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )
        # log_command_output("slither " + " ".join(command[1:]), result)
        error_type = classify_error(result)
        is_success = (result.returncode <= 255)

        generated_json = None
        if os.path.exists(output_json):
            try:
                with open(output_json, "r") as f:
                    generated_json = json.load(f)
            except Exception as e:
                generated_json = {"error": f"Could not read JSON: {str(e)}"}

        detectors = summarize_detectors(generated_json)
        response_payload = {
            "success": is_success,
            "command": command_str,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error_type": error_type if not is_success else None,
            "exit_code": result.returncode,
            "results": {
                "detectors": detectors
            }
        }
        logger.info("📤 RESPONSE TO API (RAW): %s", response_payload)
        return response_payload

    except subprocess.TimeoutExpired:
        response_payload = {
            "success": False,
            "command": command_str,
            "stdout": "",
            "stderr": "",
            "error_type": "timeout",
            "exit_code": None,
            "results": {"detectors": []}
        }
        logger.info("📤 RESPONSE TO API (RAW): %s", response_payload)
        return response_payload
    except Exception as e:
        response_payload = {
            "success": False,
            "command": command_str,
            "stdout": "",
            "stderr": str(e),
            "error_type": "unexpected_error",
            "exit_code": None,
            "results": {"detectors": []}
        }
        logger.info("📤 RESPONSE TO API (RAW): %s", response_payload)
        return response_payload

@app.get("/")
async def root():
    return {"service": "Slither Analysis", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
