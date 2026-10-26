#!/usr/bin/env bash
# Roteiro de evidências: executa todas as operações da API com cURL.
# Uso: com a API rodando em http://127.0.0.1:8000, execute:  bash exemplos_curl.sh
# Dica para o relatório: rode e salve a saída com  bash exemplos_curl.sh | tee evidencias.txt

BASE="${BASE:-http://127.0.0.1:8000}"
EMAIL="aluno$RANDOM@exemplo.com"
SENHA="senha123"

passo() { printf '\n=== %s ===\n' "$1"; }
req()   { curl -s -o /dev/stderr -w '-> HTTP %{http_code}\n' "$@" 2>&1; }

passo "1. Registrar usuário (201)"
req -X POST "$BASE/auth/register" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"senha\":\"$SENHA\"}"

passo "2. Login e obtenção do token JWT (200)"
TOKEN=$(curl -s -X POST "$BASE/auth/login" -d "username=$EMAIL&password=$SENHA" \
        | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "token obtido: ${TOKEN:0:20}..."
AUTH="Authorization: Bearer $TOKEN"

passo "3. Endpoint protegido SEM token (401)"
req "$BASE/transacoes"

passo "4. Criar categoria (201)"
req -X POST "$BASE/categorias" -H "$AUTH" -H 'Content-Type: application/json' -d '{"nome":"Alimentação"}'

passo "5. POST /transacoes - criar despesa (201)"
req -X POST "$BASE/transacoes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"descricao":"Mercado","valor":"250.50","tipo":"despesa","data":"2026-10-10","categoria_id":1}'

passo "6. POST /transacoes - criar receita (201)"
req -X POST "$BASE/transacoes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"descricao":"Salário","valor":"3500.00","tipo":"receita","data":"2026-10-05"}'

passo "7. POST com valor negativo (422)"
req -X POST "$BASE/transacoes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"descricao":"Inválida","valor":"-5","tipo":"despesa","data":"2026-10-10"}'

passo "8. POST com categoria inexistente (400)"
req -X POST "$BASE/transacoes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"descricao":"x","valor":"5","tipo":"despesa","data":"2026-10-10","categoria_id":99}'

passo "9. GET /transacoes - listagem (200)"
req "$BASE/transacoes" -H "$AUTH"

passo "10. GET /transacoes?tipo=despesa - filtro (200)"
req "$BASE/transacoes?tipo=despesa" -H "$AUTH"

passo "11. GET /transacoes/1 - individual (200)"
req "$BASE/transacoes/1" -H "$AUTH"

passo "12. GET /transacoes/999 - inexistente (404)"
req "$BASE/transacoes/999" -H "$AUTH"

passo "13. PATCH /transacoes/1 - atualização parcial (200)"
req -X PATCH "$BASE/transacoes/1" -H "$AUTH" -H 'Content-Type: application/json' -d '{"valor":"300.00"}'

passo "14. GET /transacoes/resumo - saldo (200)"
req "$BASE/transacoes/resumo" -H "$AUTH"

passo "15. DELETE /transacoes/1 (204)"
req -X DELETE "$BASE/transacoes/1" -H "$AUTH"

passo "16. DELETE novamente - já removida (404)"
req -X DELETE "$BASE/transacoes/1" -H "$AUTH"

passo "17. CORS - origem permitida (cabeçalho Access-Control-Allow-Origin presente)"
curl -s -i -X OPTIONS "$BASE/transacoes" -H 'Origin: http://localhost:3000' \
     -H 'Access-Control-Request-Method: GET' | grep -i -E 'HTTP/|access-control'

passo "18. CORS - origem NÃO permitida (sem cabeçalho Allow-Origin)"
curl -s -i -X OPTIONS "$BASE/transacoes" -H 'Origin: http://site-malicioso.com' \
     -H 'Access-Control-Request-Method: GET' | grep -i -E 'HTTP/|access-control' || echo "(nenhum cabeçalho CORS retornado)"
