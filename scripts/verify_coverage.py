#!/usr/bin/env python3
"""
scripts/verify_coverage.py
==========================
Validador estrito de cobertura de código (Branch + Line Coverage).
Lê o coverage.xml gerado pelo pytest-cov, calcula a métrica canônica consolidada
e falha com código de saída 1 (Fail-Closed) se o percentual for inferior ao limiar exigido.
"""

import sys
import os
import xml.etree.ElementTree as ET

def verify_coverage(xml_path: str = "coverage.xml", required_pct: float = 85.0) -> float:
    if not os.path.exists(xml_path):
        print(f"[ERRO] Arquivo de cobertura '{xml_path}' não encontrado.")
        sys.exit(1)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        lines_valid = int(root.attrib.get("lines-valid", 0))
        lines_covered = int(root.attrib.get("lines-covered", 0))
        branches_valid = int(root.attrib.get("branches-valid", 0))
        branches_covered = int(root.attrib.get("branches-covered", 0))
        
        total_items = lines_valid + branches_valid
        total_covered = lines_covered + branches_covered
        
        if total_items == 0:
            print("[ERRO] Nenhuma linha ou branch válida encontrada no coverage.xml.")
            sys.exit(1)
            
        coverage_pct = (total_covered / total_items) * 100.0
        
        print("=" * 80)
        print(" AUDITORIA ESTRITA DE COBERTURA DE TESTES (Branch + Statement)")
        print("=" * 80)
        print(f" Linhas Válidas:     {lines_valid}")
        print(f" Linhas Cobertas:    {lines_covered} ({(lines_covered / lines_valid * 100):.2f}%)")
        print(f" Branches Válidas:   {branches_valid}")
        print(f" Branches Cobertas:  {branches_covered} ({(branches_covered / branches_valid * 100):.2f}%)")
        print(f" Cobertura Total:    {coverage_pct:.2f}%")
        print(f" Limiar Requerido:   {required_pct:.2f}%")
        print("-" * 80)
        
        if coverage_pct < required_pct:
            print(f"[FALHA CRÍTICA] Cobertura de {coverage_pct:.2f}% abaixo do limiar obrigatório de {required_pct:.2f}%!")
            sys.exit(1)
            
        print(f"[OK] Cobertura estrita validada com sucesso: {coverage_pct:.2f}% >= {required_pct:.2f}%\n")
        return coverage_pct
    except Exception as e:
        print(f"[ERRO] Falha ao processar {xml_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"
    req = float(sys.argv[2]) if len(sys.argv) > 2 else 85.0
    verify_coverage(path, req)
