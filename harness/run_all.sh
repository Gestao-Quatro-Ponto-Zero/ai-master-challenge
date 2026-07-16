#!/usr/bin/env bash
# Churn Platform — Executa todos os harnesses de validação
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL_PASS=0
TOTAL_FAIL=0
FAILED_SPECS=()

echo "╔══════════════════════════════════════════════╗"
echo "║  Churn Platform — Spec Harness Runner        ║"
echo "╚══════════════════════════════════════════════╝"

for spec in spec-2 spec-5 spec-10 spec-11 spec-12; do
    echo ""
    echo "────────────────────────────────────────────"
    echo "  Running $spec..."
    echo "────────────────────────────────────────────"
    
    set +e
    output=$(bash "$SCRIPT_DIR/$spec.test.sh" 2>&1)
    exit_code=$?
    set -e
    
    echo "$output"
    
    passed=$(echo "$output" | grep -c "✓" || true)
    failed=$(echo "$output" | grep -c "✗" || true)
    
    TOTAL_PASS=$((TOTAL_PASS + passed))
    TOTAL_FAIL=$((TOTAL_FAIL + failed))
    
    if [ $exit_code -ne 0 ]; then
        FAILED_SPECS+=("$spec")
    fi
done

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Results                                     ║"
echo "║                                              ║"
echo "║  Total: $((TOTAL_PASS + TOTAL_FAIL)) tests                      ║"
echo "║  Pass:  $TOTAL_PASS                           ║"
echo "║  Fail:  $TOTAL_FAIL                           ║"

if [ ${#FAILED_SPECS[@]} -gt 0 ]; then
    echo "║                                              ║"
    echo "║  Failed specs: ${FAILED_SPECS[*]}            ║"
    echo "╚══════════════════════════════════════════════╝"
    exit 1
else
    echo "║  All specs passed!                           ║"
    echo "╚══════════════════════════════════════════════╝"
fi
