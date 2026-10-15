-- Dados inteiramente fictícios. Endereços de documentação.
CREATE TABLE logins (
 id INTEGER PRIMARY KEY,
 instante TEXT NOT NULL,
 usuario TEXT NOT NULL,
 ip TEXT NOT NULL,
 sucesso INTEGER NOT NULL CHECK (sucesso IN (0,1)),
 setor TEXT NOT NULL
);
INSERT INTO logins VALUES
(1,'2026-10-01 08:00:00','ana','192.0.2.10',1,'Financeiro'),
(2,'2026-10-01 23:10:00','bruno','198.51.100.23',0,'Vendas'),
(3,'2026-10-01 23:11:00','bruno','198.51.100.23',0,'Vendas'),
(4,'2026-10-01 23:12:00','bruno','198.51.100.23',0,'Vendas'),
(5,'2026-10-01 23:13:00','bruno','198.51.100.23',1,'Vendas'),
(6,'2026-10-02 09:20:00','carla','192.0.2.20',0,'Financeiro'),
(7,'2026-10-02 10:00:00','ana','192.0.2.10',1,'Financeiro'),
(8,'2026-10-02 22:15:00','davi','203.0.113.8',1,'TI');
