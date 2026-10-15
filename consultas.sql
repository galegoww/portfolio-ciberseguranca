-- Q1: falhas no intervalo [inicio, fim).
SELECT id, usuario, ip FROM logins
WHERE sucesso = 0 AND instante >= '2026-10-01 00:00:00'
AND instante < '2026-10-02 00:00:00' ORDER BY id;

-- Q2: eventos fora do expediente hipotetico [08:00, 18:00).
SELECT id, usuario FROM logins
WHERE time(instante) < '08:00:00' OR time(instante) >= '18:00:00'
ORDER BY id;

-- Q3: usuarios com tres ou mais falhas na amostra inteira.
SELECT usuario, COUNT(*) AS falhas FROM logins
WHERE sucesso = 0 GROUP BY usuario HAVING COUNT(*) >= 3
ORDER BY falhas DESC, usuario;

-- Q4: acessos bem-sucedidos do Financeiro.
SELECT id, usuario FROM logins
WHERE setor = 'Financeiro' AND sucesso = 1 ORDER BY id;
