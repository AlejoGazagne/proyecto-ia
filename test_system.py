#!/usr/bin/env python3
"""
Script de prueba para el sistema de microservicios ETH Security Toolbox
"""

import requests
import json
import time

# URL de la API
API_URL = "http://localhost:8000"

# Contrato de ejemplo con vulnerabilidad intencional
VULNERABLE_CONTRACT = """
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Vulnerabilidad: Reentrancy
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        
        (bool success, ) = msg.sender.call{value: _amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= _amount;
    }
    
    function getBalance() public view returns (uint256) {
        return balances[msg.sender];
    }
}
"""

# Contrato simple sin vulnerabilidades
SIMPLE_CONTRACT = """
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 private value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public view returns (uint256) {
        return value;
    }
}
"""

def check_health():
    """Verifica el estado de los servicios"""
    print("🔍 Verificando estado de servicios...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        result = response.json()
        
        print(f"\n📊 Estado del sistema: {result['status']}")
        print("\n🔧 Estado de microservicios:")
        for service, status in result['services'].items():
            emoji = "✅" if status == "healthy" else "❌"
            print(f"  {emoji} {service}: {status}")
        
        return result['status'] == 'healthy'
    except Exception as e:
        print(f"❌ Error al verificar salud: {e}")
        return False

def analyze_contract(code, filename="test.sol"):
    """Analiza un contrato"""
    print(f"\n🔬 Analizando contrato: {filename}")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={
                "code": code,
                "filename": filename,
                "is_production_ready": False
            },
            timeout=360  # 6 minutos
        )
        
        result = response.json()
        
        print(f"\n📋 ID de análisis: {result['analysis_id']}")
        print(f"📄 Archivo: {result['filename']}")
        print(f"✅ Éxito general: {result['success']}")
        print(f"⚠️  Errores críticos: {result['has_critical_errors']}")
        
        if result['tools_with_errors']:
            print(f"🔴 Herramientas con errores: {', '.join(result['tools_with_errors'])}")
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS POR HERRAMIENTA")
        print("=" * 60)
        
        for tool, data in result['results'].items():
            print(f"\n🔧 {tool.upper()}")
            print("-" * 40)
            
            if isinstance(data, dict):
                if 'success' in data:
                    status = "✅ Exitoso" if data['success'] else "❌ Falló"
                    print(f"  Estado: {status}")
                
                if 'error_type' in data and data['error_type']:
                    print(f"  Tipo de error: {data['error_type']}")
                
                if 'exit_code' in data:
                    print(f"  Código de salida: {data['exit_code']}")
                
                # Mostrar primeras líneas de stdout si existe
                if 'stdout' in data and data['stdout']:
                    stdout_preview = data['stdout'][:200]
                    print(f"  Output: {stdout_preview}...")
                
                # Mostrar si encontró vulnerabilidades
                if tool == 'slither' and 'generated_json' in data and data['generated_json']:
                    try:
                        if isinstance(data['generated_json'], dict):
                            results = data['generated_json'].get('results', {})
                            detectors = results.get('detectors', [])
                            print(f"  🔍 Vulnerabilidades encontradas: {len(detectors)}")
                            
                            for detector in detectors[:3]:  # Mostrar primeras 3
                                impact = detector.get('impact', 'unknown')
                                check = detector.get('check', 'unknown')
                                print(f"    - {impact}: {check}")
                    except:
                        pass
        
        return result
        
    except requests.Timeout:
        print("⏱️  Timeout: El análisis tardó más de lo esperado")
        return None
    except Exception as e:
        print(f"❌ Error al analizar: {e}")
        return None

def main():
    print("=" * 60)
    print("ETH SECURITY TOOLBOX - TEST SUITE")
    print("=" * 60)
    
    # 1. Verificar salud del sistema
    if not check_health():
        print("\n⚠️  ADVERTENCIA: Algunos servicios no están saludables")
        print("Continuando de todas formas...")
        time.sleep(2)
    
    # 2. Analizar contrato vulnerable
    print("\n" + "=" * 60)
    print("TEST 1: Contrato con vulnerabilidad de Reentrancy")
    print("=" * 60)
    analyze_contract(VULNERABLE_CONTRACT, "vulnerable_bank.sol")
    
    time.sleep(2)
    
    # 3. Analizar contrato simple
    print("\n" + "=" * 60)
    print("TEST 2: Contrato simple sin vulnerabilidades")
    print("=" * 60)
    analyze_contract(SIMPLE_CONTRACT, "simple_storage.sol")
    
    print("\n" + "=" * 60)
    print("✅ TESTS COMPLETADOS")
    print("=" * 60)
    print("\n📚 Documentación interactiva disponible en:")
    print(f"   {API_URL}/docs")

if __name__ == "__main__":
    main()
