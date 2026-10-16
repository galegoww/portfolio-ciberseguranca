import time, json, math, io, os, sqlite3, random, socket, asyncio, re, urllib.request, urllib.parse
from collections import Counter, deque
import threading
from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# DNS e ML
from dnslib.server import DNSServer, BaseResolver
from dnslib import DNSRecord, RCODE, QTYPE
from sklearn.ensemble import RandomForestClassifier
import joblib

app = FastAPI(title="DNS AI Shield ULTRA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO ---
BASE_DIR = os.environ.get("DNS_SHIELD_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
os.makedirs(BASE_DIR, exist_ok=True)
DB_FILE = os.path.join(BASE_DIR, "dns_ai.db")
# Compatibilidade: se o arquivo baixado/duplicado estiver como dns_ai(1).db, use-o
# somente quando dns_ai.db não existir.
DB_FILE_ALTERNATIVO = os.path.join(BASE_DIR, "dns_ai(1).db")
if not os.path.exists(DB_FILE) and os.path.exists(DB_FILE_ALTERNATIVO):
    DB_FILE = DB_FILE_ALTERNATIVO

MODEL_FILE = os.path.join(BASE_DIR, "ml_model.pkl")
UPSTREAM_DNS = ("8.8.8.8", 53)
HISTORICO_MAX = 500
DNS_TIMEOUT = 2.0
HISTORICO_DB_MAX = 100000
LIST_UPDATE_INTERVAL = 6 * 60 * 60  # 6 horas
MAX_LIST_BYTES = 25 * 1024 * 1024  # 25 MB
HEALTHCHECK_DOMAIN = "dns-shield-health.local"
historico = deque(maxlen=HISTORICO_MAX)
historico_lock = threading.Lock()
conexoes_ativas = []


# --- BANCO DE DADOS E HISTÓRICO PERSISTENTE ---
def conectar_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = conectar_db()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("CREATE TABLE IF NOT EXISTS aprendizado (dominio TEXT PRIMARY KEY, status TEXT, score REAL)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historico_dns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                tempo TEXT NOT NULL,
                dominio TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 0,
                origem TEXT,
                regra TEXT,
                tipo TEXT,
                lat REAL,
                lon REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_dominio ON historico_dns(dominio)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_status ON historico_dns(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_id ON historico_dns(id DESC)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fontes_listas (
                url TEXT PRIMARY KEY,
                nome TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                ultima_atualizacao TEXT,
                total_dominios INTEGER NOT NULL DEFAULT 0,
                ultimo_erro TEXT DEFAULT ''
            )
        """)
        # Evita crescimento infinito do histórico ao longo de meses de uso.
        total = conn.execute("SELECT COUNT(*) FROM historico_dns").fetchone()[0]
        if total > HISTORICO_DB_MAX:
            conn.execute(
                "DELETE FROM historico_dns WHERE id NOT IN (SELECT id FROM historico_dns ORDER BY id DESC LIMIT ?)",
                (HISTORICO_DB_MAX,),
            )
        conn.commit()
    finally:
        conn.close()


def normalizar_dominio(dominio):
    """Normaliza URL/host para o formato salvo no banco."""
    dom = str(dominio).lower().strip()
    dom = dom.replace("https://", "").replace("http://", "")
    dom = dom.split("/", 1)[0]
    dom = dom.split(":", 1)[0]
    return dom.rstrip(".")


def salvar_db(d, status, score=0):
    dom = normalizar_dominio(d)
    if not dom:
        return ""
    conn = conectar_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO aprendizado (dominio, status, score) VALUES (?, ?, ?)",
            (dom, status, score),
        )
        conn.commit()
    finally:
        conn.close()
    return dom


def persistir_deteccao(dominio, resultado):
    # Só persiste novas detecções da IA. Regras herdadas não duplicam a blacklist.
    if resultado.get("status") != "MALWARE" or resultado.get("origem") != "ML":
        return
    salvar_db(dominio, resultado["status"], resultado["score"])


def registrar_evento(dominio, status, score, origem="", regra="", tipo=""):
    agora = time.strftime("%Y-%m-%d %H:%M:%S")
    evento = {
        "dominio": normalizar_dominio(dominio),
        "status": status,
        "score": float(score or 0.0),
        "tempo": agora[-8:],
        "lat": -26.22 + random.uniform(-2, 2),
        "lon": -52.67 + random.uniform(-2, 2),
        "bloqueado": status == "MALWARE",
        "origem": origem or "",
        "regra": regra or "",
        "tipo": tipo or "",
    }

    with historico_lock:
        historico.appendleft(evento)

    try:
        conn = conectar_db()
        conn.execute(
            """
            INSERT INTO historico_dns
                (data_hora, tempo, dominio, status, score, origem, regra, tipo, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agora, evento["tempo"], evento["dominio"], evento["status"], evento["score"],
                evento["origem"], evento["regra"], evento["tipo"], evento["lat"], evento["lon"],
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[HISTÓRICO] Falha ao persistir evento: {exc}")

    return evento


def obter_historico(limite=HISTORICO_MAX):
    try:
        conn = conectar_db()
        rows = conn.execute(
            """
            SELECT tempo, dominio, status, score, origem, regra, tipo, lat, lon
            FROM historico_dns
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limite),),
        ).fetchall()
        conn.close()
        return [
            {
                "tempo": r["tempo"], "dominio": r["dominio"], "status": r["status"],
                "score": float(r["score"] or 0.0), "origem": r["origem"] or "",
                "regra": r["regra"] or "", "tipo": r["tipo"] or "",
                "lat": float(r["lat"] or -26.22), "lon": float(r["lon"] or -52.67),
                "bloqueado": r["status"] == "MALWARE",
            }
            for r in rows
        ]
    except Exception:
        with historico_lock:
            return list(historico)[:limite]


def estatisticas_dominios(limite=8):
    conn = conectar_db()
    try:
        rows = conn.execute(
            """
            SELECT dominio,
                   COUNT(*) AS total,
                   SUM(CASE WHEN status='MALWARE' THEN 1 ELSE 0 END) AS bloqueios
            FROM historico_dns
            GROUP BY dominio
            ORDER BY total DESC, bloqueios DESC
            LIMIT ?
            """,
            (int(limite),),
        ).fetchall()
        return [
            {"dominio": r["dominio"], "total": int(r["total"]), "bloqueios": int(r["bloqueios"] or 0)}
            for r in rows
        ]
    finally:
        conn.close()


TRACKING_HINTS = (
    "track", "tracking", "analytics", "pixel", "telemetry", "metrics", "beacon",
    "doubleclick", "googlesyndication", "adservice", "adserver", "ads.", "ads-",
    "advert", "affiliate", "sponsor", "measure", "counter"
)


def estatisticas_tempo_real(minutos=10):
    """Agrupa requisições e bloqueios por minuto para o gráfico em tempo real."""
    minutos = max(1, min(int(minutos), 120))
    conn = conectar_db()
    try:
        rows = conn.execute(
            """
            SELECT substr(data_hora, 12, 5) AS hora,
                   COUNT(*) AS total,
                   SUM(CASE WHEN status='MALWARE' THEN 1 ELSE 0 END) AS bloqueios,
                   MIN(id) AS primeiro_id
            FROM historico_dns
            WHERE data_hora >= datetime('now', 'localtime', ?)
            GROUP BY substr(data_hora, 1, 16)
            ORDER BY primeiro_id ASC
            """,
            (f"-{minutos} minutes",),
        ).fetchall()
        return [
            {"hora": r["hora"], "total": int(r["total"] or 0), "bloqueios": int(r["bloqueios"] or 0)}
            for r in rows
        ]
    finally:
        conn.close()


def estatisticas_bloqueios_recentes(minutos=10):
    """Classifica bloqueios recentes em rastreio/ads, IA e blacklist.

    A categoria rastreio/ads é uma heurística baseada no nome do domínio,
    não inspeção do conteúdo do tráfego.
    """
    minutos = max(1, min(int(minutos), 120))
    conn = conectar_db()
    try:
        rows = conn.execute(
            """
            SELECT dominio, origem
            FROM historico_dns
            WHERE status='MALWARE'
              AND data_hora >= datetime('now', 'localtime', ?)
            """,
            (f"-{minutos} minutes",),
        ).fetchall()
    finally:
        conn.close()

    stats = {"rastreio_ads": 0, "ia": 0, "blacklist": 0}
    for r in rows:
        dominio = (r["dominio"] or "").lower()
        origem = (r["origem"] or "").upper()
        if any(chave in dominio for chave in TRACKING_HINTS):
            stats["rastreio_ads"] += 1
        elif origem == "ML":
            stats["ia"] += 1
        else:
            stats["blacklist"] += 1
    return stats


def estatisticas_tipos_dns(minutos=10, limite=5):
    minutos = max(1, min(int(minutos), 120))
    limite = max(1, min(int(limite), 10))
    conn = conectar_db()
    try:
        rows = conn.execute(
            """
            SELECT COALESCE(NULLIF(tipo, ''), 'OUTRO') AS tipo, COUNT(*) AS total
            FROM historico_dns
            WHERE data_hora >= datetime('now', 'localtime', ?)
            GROUP BY COALESCE(NULLIF(tipo, ''), 'OUTRO')
            ORDER BY total DESC
            LIMIT ?
            """,
            (f"-{minutos} minutes", limite),
        ).fetchall()
        return [{"tipo": r["tipo"], "total": int(r["total"] or 0)} for r in rows]
    finally:
        conn.close()


init_db()

# --- MOTOR DE IA ---
def extrair_features(dom):
    return [len(dom), sum(c.isdigit() for c in dom), dom.count("-"), dom.count("."),
            sum(dom.count(c)/len(dom)*math.log2(dom.count(c)/len(dom)) for c in set(dom)) * -1]

if not os.path.exists(MODEL_FILE):
    X = [extrair_features(d) for d, l in [("google.com", 0), ("facebook.com", 0), ("malware-site.net", 1), ("x1j-z92.xyz", 1)]]
    y = [0, 0, 1, 1]
    model = RandomForestClassifier()
    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)

model = joblib.load(MODEL_FILE)

def analisar_dominio(dominio):
    dom = normalizar_dominio(dominio)
    if not dom:
        return {"status": "SAFE", "score": 0.0, "origem": "INVALID"}

    # Verifica o host exato e seus domínios-pai.
    # Ex.: www.adsense.google.com ->
    # www.adsense.google.com, adsense.google.com, google.com
    partes = [p for p in dom.split(".") if p]
    candidatos = [
        ".".join(partes[i:])
        for i in range(max(1, len(partes) - 1))
    ]

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        placeholders = ",".join("?" for _ in candidatos)

        # A regra manual mais específica vence, seja MALWARE (bloquear) ou SAFE (liberar).
        # Ex.: facebook.com=SAFE libera seus subdomínios, mas ads.facebook.com=MALWARE
        # pode ser usado depois para bloquear somente esse host específico.
        r = conn.execute(
            f"""
            SELECT dominio, status, score
            FROM aprendizado
            WHERE dominio IN ({placeholders})
            ORDER BY LENGTH(dominio) DESC
            LIMIT 1
            """,
            candidatos,
        ).fetchone()

        if r:
            status_regra = str(r[1]).upper()
            if status_regra == "MALWARE":
                return {
                    "status": "MALWARE",
                    "score": float(r[2] or 1.0),
                    "origem": "BLACKLIST",
                    "regra": r[0],
                }
            if status_regra == "SAFE":
                return {
                    "status": "SAFE",
                    "score": float(r[2] or 0.0),
                    "origem": "WHITELIST",
                    "regra": r[0],
                }
    finally:
        conn.close()

    prob = model.predict_proba([extrair_features(dom)])[0][1]
    status = "MALWARE" if prob > 0.5 else "SAFE"
    return {"status": status, "score": round(float(prob), 2), "origem": "ML"}

# --- IMPORTAÇÃO DE LISTAS PI-HOLE / ADGUARD ---
DOMINIO_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.I,
)


def dominio_valido(dominio):
    dom = normalizar_dominio(dominio)
    return bool(dom and DOMINIO_RE.match(dom))


def extrair_dominio_linha(linha):
    linha = linha.strip()
    if not linha or linha.startswith(("#", "!", "[", "@@")):
        return None

    # Remove comentários de listas hosts.
    if " #" in linha:
        linha = linha.split(" #", 1)[0].strip()

    # Formato AdGuard/AdBlock: ||ads.exemplo.com^
    if linha.startswith("||"):
        candidato = linha[2:].split("^", 1)[0].split("$", 1)[0]
    else:
        partes = linha.split()
        if len(partes) >= 2 and partes[0] in {"0.0.0.0", "127.0.0.1", "::", "::1"}:
            candidato = partes[1]
        else:
            candidato = partes[0]

    candidato = candidato.strip().lstrip("|").rstrip("|")
    candidato = candidato.split("^", 1)[0].split("$", 1)[0]
    candidato = candidato.lstrip("*.")
    dom = normalizar_dominio(candidato)
    return dom if dominio_valido(dom) else None


def coberto_por_whitelist(dominio, whitelist):
    partes = dominio.split(".")
    for i in range(max(1, len(partes) - 1)):
        if ".".join(partes[i:]) in whitelist:
            return True
    return dominio in whitelist


def importar_conteudo_lista(texto):
    dominios = set()
    for linha in texto.splitlines():
        dom = extrair_dominio_linha(linha)
        if dom:
            dominios.add(dom)

    conn = conectar_db()
    try:
        whitelist = {
            r[0] for r in conn.execute("SELECT dominio FROM aprendizado WHERE status='SAFE'").fetchall()
        }
        permitidos = sorted(d for d in dominios if not coberto_por_whitelist(d, whitelist))
        ignorados = len(dominios) - len(permitidos)

        conn.executemany(
            "INSERT OR IGNORE INTO aprendizado (dominio, status, score) VALUES (?, 'MALWARE', 1.0)",
            [(d,) for d in permitidos],
        )
        conn.executemany(
            "UPDATE aprendizado SET status='MALWARE', score=1.0 WHERE dominio=? AND status!='SAFE'",
            [(d,) for d in permitidos],
        )
        conn.commit()
        return {"total": len(dominios), "importados": len(permitidos), "whitelist_ignorada": ignorados}
    finally:
        conn.close()


def baixar_lista(url):
    url = str(url).strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Informe uma URL http:// ou https:// válida.")

    req = urllib.request.Request(url, headers={"User-Agent": "DNS-AI-Shield/2.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        tamanho = resp.headers.get("Content-Length")
        if tamanho and int(tamanho) > MAX_LIST_BYTES:
            raise ValueError("Lista maior que 25 MB.")
        conteudo = resp.read(MAX_LIST_BYTES + 1)
        if len(conteudo) > MAX_LIST_BYTES:
            raise ValueError("Lista maior que 25 MB.")
    return conteudo.decode("utf-8", errors="ignore")


def importar_lista_url(url):
    texto = baixar_lista(url)
    resultado = importar_conteudo_lista(texto)
    nome = urllib.parse.urlparse(url).netloc or "lista"
    agora = time.strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar_db()
    try:
        conn.execute(
            """
            INSERT INTO fontes_listas (url, nome, ativo, ultima_atualizacao, total_dominios, ultimo_erro)
            VALUES (?, ?, 1, ?, ?, '')
            ON CONFLICT(url) DO UPDATE SET
                nome=excluded.nome, ativo=1, ultima_atualizacao=excluded.ultima_atualizacao,
                total_dominios=excluded.total_dominios, ultimo_erro=''
            """,
            (url, nome, agora, resultado["importados"]),
        )
        conn.commit()
    finally:
        conn.close()

    resultado["url"] = url
    return resultado


def atualizar_fontes_automaticamente():
    conn = conectar_db()
    try:
        urls = [r[0] for r in conn.execute("SELECT url FROM fontes_listas WHERE ativo=1").fetchall()]
    finally:
        conn.close()

    for url in urls:
        try:
            resultado = importar_lista_url(url)
            print(f"[LISTA] Atualizada: {url} | {resultado['importados']} domínios")
        except Exception as exc:
            print(f"[LISTA ERRO] {url}: {exc}")
            conn = conectar_db()
            try:
                conn.execute(
                    "UPDATE fontes_listas SET ultimo_erro=?, ultima_atualizacao=? WHERE url=?",
                    (str(exc)[:500], time.strftime("%Y-%m-%d %H:%M:%S"), url),
                )
                conn.commit()
            finally:
                conn.close()


def loop_atualizacao_listas():
    # Aguarda o servidor iniciar e depois atualiza fontes salvas a cada 6 horas.
    time.sleep(10)
    while True:
        atualizar_fontes_automaticamente()
        time.sleep(LIST_UPDATE_INTERVAL)


_dns_status_cache = {"ts": 0.0, "online": False}
_dns_status_lock = threading.Lock()


def verificar_dns_local():
    agora = time.time()
    with _dns_status_lock:
        if agora - _dns_status_cache["ts"] < 2.0:
            return _dns_status_cache["online"]

    online = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.6)
    try:
        consulta = DNSRecord.question(HEALTHCHECK_DOMAIN)
        sock.sendto(consulta.pack(), ("127.0.0.1", 53))
        data, _ = sock.recvfrom(4096)
        DNSRecord.parse(data)
        online = True
    except Exception:
        online = False
    finally:
        sock.close()

    with _dns_status_lock:
        _dns_status_cache["ts"] = agora
        _dns_status_cache["online"] = online
    return online


# --- WEBSOCKET ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conexoes_ativas.append(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in conexoes_ativas: conexoes_ativas.remove(websocket)

async def disparar_atualizacao():
    for c in conexoes_ativas:
        try: await c.send_text("update")
        except: continue

# --- DASHBOARD HTML ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8"><title>DNS AI Shield ULTRA</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { background: #020617; color: white; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
            .card { background: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 20px; }
            .grid-main { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
            .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
            .h-stat { font-size: 28px; font-weight: bold; color: #22d3ee; margin: 0; }
            table { width: 100%; border-collapse: collapse; }
            th { text-align: left; color: #64748b; font-size: 11px; padding: 10px; border-bottom: 1px solid #1e293b; }
            td { padding: 12px 10px; border-bottom: 1px solid #0f172a; font-size: 12px; }
            .badge-MALWARE { color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 4px; font-weight: bold; }
            .badge-SAFE { color: #22c55e; background: rgba(34, 197, 94, 0.1); padding: 4px 8px; border-radius: 4px; font-weight: bold; }
            .btn-action { border: none; padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 10px; font-weight: bold; color: white; transition: 0.3s; }
            .btn-bloq { background: #ef4444; }
            .btn-bloq:hover { background: #dc2626; }
            .btn-liberar { background: #16a34a; }
            .btn-liberar:hover { background: #15803d; }
            .controle-dominio { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
            .controle-dominio input { flex: 1; min-width: 210px; background: #020617; color: white; border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; outline: none; }
            .controle-dominio input:focus { border-color: #22d3ee; }
            .ajuda-controle { color: #94a3b8; font-size: 11px; margin: 8px 0 0 0; line-height: 1.4; }
            .quick-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
            .btn-quick { background: #1e293b; border: 1px solid #334155; }
            .btn-quick:hover { background: #334155; }
            .telemetry-card { height: 300px; padding: 14px; box-sizing: border-box; overflow: hidden; }
            .telemetry-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
            .telemetry-title { margin:0; font-size:14px; color:#e2e8f0; }
            .telemetry-subtitle { color:#64748b; font-size:9px; margin-top:2px; }
            .live-pill { display:flex; align-items:center; gap:6px; padding:4px 8px; border-radius:999px; background:#052e2b; color:#34d399; font-size:9px; font-weight:700; border:1px solid #065f46; }
            .live-dot { width:7px; height:7px; border-radius:50%; background:#22c55e; box-shadow:0 0 10px #22c55e; animation:pulseLive 1.5s infinite; }
            @keyframes pulseLive { 0%,100% { opacity:1; } 50% { opacity:.35; } }
            .telemetry-grid { display:grid; grid-template-columns:minmax(0, 1.75fr) minmax(230px, .9fr); gap:10px; height:235px; }
            .telemetry-main, .mini-chart-box { background:#020617; border:1px solid #1e293b; border-radius:10px; }
            .telemetry-main { padding:10px 12px 8px; min-width:0; }
            .telemetry-side { display:grid; grid-template-rows:1fr 1fr; gap:10px; min-width:0; }
            .mini-chart-box { padding:7px 9px; min-height:0; }
            .chart-panel-title { display:flex; justify-content:space-between; align-items:center; gap:8px; color:#94a3b8; font-size:10px; margin-bottom:4px; }
            .chart-panel-title b { color:#22d3ee; font-size:10px; }
            .chart-wrap-large { position:relative; height:195px; }
            .chart-wrap-mini { position:relative; height:82px; }
            @media (max-width: 980px) {
                .grid-main { grid-template-columns:1fr; }
                .telemetry-card { height:auto; }
                .telemetry-grid { grid-template-columns:1fr; height:auto; }
                .telemetry-side { grid-template-columns:1fr 1fr; grid-template-rows:none; }
                .chart-wrap-large { height:220px; }
                .chart-wrap-mini { height:130px; }
            }
            
            .log-txt { background: #020617; color: #22d3ee; font-family: monospace; font-size: 10px; height: 150px; overflow-y: auto; padding: 10px; border: 1px dashed #1e293b; }
            
            /* Lista de Bloqueados Estilizada */
            .blacklist-container { height: 200px; overflow-y: auto; margin-top: 10px; }
            .blacklist-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #1e293b; font-size: 11px; }
            .blacklist-item:hover { background: rgba(255,255,255,0.05); }
        </style>
    </head>
    <body>
        <h1 style="color: #22d3ee; margin-bottom:20px;">🛡️ DNS AI SHIELD ULTRA PRO</h1>
        <div class="stat-grid">
            <div class="card"><p class="h-stat" id="total-req">0</p><span>Requisições</span></div>
            <div class="card"><p class="h-stat" id="total-bloq" style="color:#ef4444;">0</p><span>Bloqueios IA</span></div>
            <div class="card"><p class="h-stat" id="dns-status" style="color:#f59e0b;">VERIFICANDO</p><span>Servidor DNS + Machine Learning</span></div>
        </div>
        <div class="grid-main">
            <div>
                <div class="card telemetry-card">
                    <div class="telemetry-header">
                        <div>
                            <h3 class="telemetry-title">📡 Monitoramento DNS em tempo real</h3>
                            <div class="telemetry-subtitle">Atividade dos últimos 10 minutos — atualização automática</div>
                        </div>
                        <div class="live-pill"><span class="live-dot"></span> AO VIVO</div>
                    </div>
                    <div class="telemetry-grid">
                        <div class="telemetry-main">
                            <div class="chart-panel-title"><span>Tráfego DNS</span><b id="traffic-now">0 consultas</b></div>
                            <div class="chart-wrap-large"><canvas id="trafficChart"></canvas></div>
                        </div>
                        <div class="telemetry-side">
                            <div class="mini-chart-box">
                                <div class="chart-panel-title"><span>Rastreio / Ads bloqueados</span><b id="tracking-count">0</b></div>
                                <div class="chart-wrap-mini"><canvas id="securityChart"></canvas></div>
                            </div>
                            <div class="mini-chart-box">
                                <div class="chart-panel-title"><span>Tipos de consulta DNS</span><b id="dns-types-count">0 tipos</b></div>
                                <div class="chart-wrap-mini"><canvas id="dnsTypeChart"></canvas></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <table>
                        <thead><tr><th>Hora</th><th>Domínio</th><th>Status</th><th>Score</th><th>Ação</th></tr></thead>
                        <tbody id="log-table"></tbody>
                    </table>
                </div>
            </div>
            <div>
                <div class="card" style="border-color:#334155;">
                    <h3 style="font-size: 15px; margin: 0; color: #22d3ee;">🎛️ Controle manual de domínio</h3>
                    <p class="ajuda-controle">Digite um domínio, por exemplo <b>facebook.com</b> ou <b>youtube.com</b>. Liberar cria uma regra SAFE para o domínio e seus subdomínios.</p>
                    <div class="controle-dominio">
                        <input id="dominio-manual" type="text" placeholder="facebook.com" autocomplete="off">
                        <button type="button" class="btn-action btn-bloq" onclick="acaoDominio('/bloquear_manual')">🚫 BLOQUEAR</button>
                        <button type="button" class="btn-action btn-liberar" onclick="acaoDominio('/desbloquear')">✅ LIBERAR</button>
                    </div>
                    <div class="quick-actions">
                        <button type="button" class="btn-action btn-quick" onclick="liberarPreset('facebook')">✅ Liberar Facebook</button>
                        <button type="button" class="btn-action btn-quick" onclick="liberarPreset('youtube')">✅ Liberar YouTube</button>
                    </div>
                </div>

                <div class="card">
                    <h3 style="font-size: 14px; margin: 0; color: #ef4444;">🚫 Gerenciar Blacklist (<span id="count-bloqueados">0</span>)</h3>
                    <div id="blacklist-list" class="blacklist-container"></div>
                </div>

                <div class="card"><canvas id="mainChart"></canvas></div>
                
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h3 style="font-size: 14px; margin: 0;">Explorador TXT (Pi-hole)</h3>
                        <a href="/download_pihole" class="btn-action" style="background: #22d3ee; color: #020617; text-decoration: none; padding: 4px 8px;">📥 Baixar</a>
                    </div>
                    <div id="pihole-log" class="log-txt"></div>
                    <div class="controle-dominio" style="margin-top:10px;">
                        <input id="lista-url" type="text" placeholder="URL de lista Pi-hole / AdGuard" autocomplete="off">
                        <button type="button" class="btn-action btn-quick" onclick="importarLista()">⬇️ IMPORTAR</button>
                    </div>
                    <p id="lista-status" class="ajuda-controle">Fontes adicionadas são atualizadas automaticamente a cada 6 horas.</p>
                </div>
            </div>
        </div>
        <script>
            const ws = new WebSocket(`ws://${location.host}/ws`);
            const mainChart = new Chart(document.getElementById('mainChart'), {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [
                        {label: 'Requisições', data: [], backgroundColor: 'rgba(34,211,238,0.55)'},
                        {label: 'Bloqueios', data: [], backgroundColor: 'rgba(239,68,68,0.65)'}
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {legend: {labels: {color: '#cbd5e1'}}},
                    scales: {
                        x: {ticks: {color: '#94a3b8'}},
                        y: {beginAtZero: true, ticks: {color: '#94a3b8'}}
                    }
                }
            });

            const trafficChart = new Chart(document.getElementById('trafficChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Requisições', data: [], borderColor: '#22d3ee',
                            backgroundColor: 'rgba(34,211,238,0.10)', fill: true,
                            tension: 0.35, pointRadius: 1.5, borderWidth: 2
                        },
                        {
                            label: 'Bloqueios', data: [], borderColor: '#ef4444',
                            backgroundColor: 'rgba(239,68,68,0.06)', fill: true,
                            tension: 0.35, pointRadius: 1.5, borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, animation: {duration: 250},
                    interaction: {mode: 'index', intersect: false},
                    plugins: {
                        legend: {position: 'top', align: 'end', labels: {color:'#94a3b8', boxWidth:9, boxHeight:9, font:{size:9}}},
                        tooltip: {enabled: true}
                    },
                    scales: {
                        x: {grid:{color:'rgba(51,65,85,.25)'}, ticks:{color:'#64748b', font:{size:8}, maxRotation:0}},
                        y: {beginAtZero:true, grid:{color:'rgba(51,65,85,.25)'}, ticks:{color:'#64748b', precision:0, font:{size:8}}}
                    }
                }
            });

            const securityChart = new Chart(document.getElementById('securityChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Rastreio/Ads', 'IA', 'Blacklist'],
                    datasets: [{data:[0,0,0], backgroundColor:['#f59e0b','#a855f7','#ef4444'], borderWidth:0}]
                },
                options: {
                    responsive:true, maintainAspectRatio:false, cutout:'66%', animation:{duration:250},
                    plugins:{legend:{position:'right', labels:{color:'#94a3b8', boxWidth:7, boxHeight:7, padding:5, font:{size:8}}}}
                }
            });

            const dnsTypeChart = new Chart(document.getElementById('dnsTypeChart'), {
                type: 'bar',
                data: {labels:[], datasets:[{label:'Consultas', data:[], backgroundColor:'rgba(34,211,238,.58)', borderRadius:4}]},
                options: {
                    indexAxis:'y', responsive:true, maintainAspectRatio:false, animation:{duration:250},
                    plugins:{legend:{display:false}},
                    scales:{
                        x:{beginAtZero:true, grid:{color:'rgba(51,65,85,.22)'}, ticks:{color:'#64748b', precision:0, font:{size:8}}},
                        y:{grid:{display:false}, ticks:{color:'#94a3b8', font:{size:8}}}
                    }
                }
            });

            function escapeHtml(value) {
                return String(value).replace(/[&<>"']/g, char => ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                }[char]));
            }
            
            async function acaoDominio(rota) {
                const input = document.getElementById('dominio-manual');
                const dominio = input.value.trim();
                if (!dominio) {
                    alert('Digite um domínio. Exemplo: facebook.com');
                    input.focus();
                    return;
                }

                const body = new URLSearchParams();
                body.append('dominio', dominio);

                try {
                    const resp = await fetch(rota, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: body.toString(),
                        redirect: 'follow'
                    });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    input.value = '';
                    await carregarDados();
                } catch (e) {
                    alert('Erro ao alterar domínio: ' + e.message);
                }
            }

            async function liberarPreset(preset) {
                const body = new URLSearchParams();
                body.append('preset', preset);
                try {
                    const resp = await fetch('/liberar_preset', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: body.toString(),
                        redirect: 'follow'
                    });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    await carregarDados();
                    alert(preset === 'facebook' ? 'Facebook liberado.' : 'YouTube liberado.');
                } catch (e) {
                    alert('Erro ao liberar serviço: ' + e.message);
                }
            }

            async function importarLista() {
                const input = document.getElementById('lista-url');
                const status = document.getElementById('lista-status');
                const url = input.value.trim();
                if (!url) {
                    alert('Cole a URL de uma lista Pi-hole/AdGuard.');
                    input.focus();
                    return;
                }
                status.innerText = 'Importando lista...';
                const body = new URLSearchParams();
                body.append('url', url);
                try {
                    const resp = await fetch('/importar_lista', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: body.toString()
                    });
                    const data = await resp.json();
                    if (!data.ok) throw new Error(data.erro || 'Falha na importação');
                    status.innerText = `Importados ${data.importados} domínios; ${data.whitelist_ignorada} preservados pela whitelist.`;
                    input.value = '';
                    await carregarDados();
                } catch (e) {
                    status.innerText = 'Erro: ' + e.message;
                }
            }

            document.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter' && document.activeElement?.id === 'dominio-manual') {
                    acaoDominio('/desbloquear');
                }
            });

            ws.onmessage = () => carregarDados();
            async function carregarDados() {
                const res = await fetch('/api/stats_completa');
                const data = await res.json();
                
                document.getElementById('total-req').innerText = data.total_req;
                document.getElementById('total-bloq').innerText = data.total_bloq;

                const dnsStatus = document.getElementById('dns-status');
                dnsStatus.innerText = data.dns_online ? 'DNS ONLINE' : 'DNS OFFLINE';
                dnsStatus.style.color = data.dns_online ? '#22c55e' : '#ef4444';

                const tempoReal = data.tempo_real || [];
                trafficChart.data.labels = tempoReal.map(x => x.hora);
                trafficChart.data.datasets[0].data = tempoReal.map(x => x.total);
                trafficChart.data.datasets[1].data = tempoReal.map(x => x.bloqueios);
                trafficChart.update('none');
                const totalJanela = tempoReal.reduce((acc, x) => acc + Number(x.total || 0), 0);
                document.getElementById('traffic-now').innerText = `${totalJanela} consultas`;

                const seg = data.bloqueios_recentes || {};
                securityChart.data.datasets[0].data = [
                    Number(seg.rastreio_ads || 0),
                    Number(seg.ia || 0),
                    Number(seg.blacklist || 0)
                ];
                securityChart.update('none');
                document.getElementById('tracking-count').innerText = Number(seg.rastreio_ads || 0);

                const tipos = data.tipos_dns || [];
                dnsTypeChart.data.labels = tipos.map(x => x.tipo);
                dnsTypeChart.data.datasets[0].data = tipos.map(x => x.total);
                dnsTypeChart.update('none');
                document.getElementById('dns-types-count').innerText = `${tipos.length} tipos`;

                const tops = data.top_dominios || [];
                mainChart.data.labels = tops.map(x => x.dominio);
                mainChart.data.datasets[0].data = tops.map(x => x.total);
                mainChart.data.datasets[1].data = tops.map(x => x.bloqueios);
                mainChart.update();
                
                // Tabela Principal
                document.getElementById('log-table').innerHTML = data.historico.map(h => `
                    <tr>
                        <td>${escapeHtml(h.tempo)}</td><td>${escapeHtml(h.dominio)}</td>
                        <td><span class="badge-${escapeHtml(h.status)}">${escapeHtml(h.status)}</span></td>
                        <td><b>${h.score}</b></td>
                        <td>
                            <form action="${h.status === 'MALWARE' ? '/desbloquear' : '/bloquear_manual'}" method="post" style="display:inline;">
                                <input type="hidden" name="dominio" value="${escapeHtml(h.dominio)}">
                                <button class="btn-action ${h.status === 'MALWARE' ? 'btn-liberar' : 'btn-bloq'}">${h.status === 'MALWARE' ? 'LIBERAR' : 'BLOQUEAR'}</button>
                            </form>
                        </td>
                    </tr>`).join('');

                // Gerenciador de Blacklist (Lista de 100 sites ou mais)
                const resBloq = await fetch('/api/bloqueados_full');
                const bloqData = await resBloq.json();
                document.getElementById('count-bloqueados').innerText = bloqData.length;
                document.getElementById('blacklist-list').innerHTML = bloqData.map(dom => `
                    <div class="blacklist-item">
                        <span>${escapeHtml(dom)}</span>
                        <form action="/desbloquear" method="post">
                            <input type="hidden" name="dominio" value="${escapeHtml(dom)}">
                            <button class="btn-action btn-liberar" style="padding: 2px 8px; font-size: 9px;">Liberar</button>
                        </form>
                    </div>
                `).join('');

                // Explorador TXT
                const piholeLog = document.getElementById('pihole-log');
                piholeLog.innerHTML = data.historico.map(h => `> [${escapeHtml(h.tempo)}] ${escapeHtml(h.status.padEnd(7))} | ${escapeHtml(h.dominio)}`).join('<br>');

            }
            carregarDados();
            setInterval(carregarDados, 5000);
        </script>
    </body>
    </html>
    """

# --- ROTAS DE API ---

@app.get("/api/bloqueados")
def api_bloqueados():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    r = conn.execute("SELECT dominio FROM aprendizado WHERE status='MALWARE' ORDER BY dominio ASC").fetchall()
    conn.close()
    return {"bloqueados": [x[0] for x in r]}

@app.get("/api/status")
def api_status():
    conn = conectar_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM aprendizado WHERE status='MALWARE'").fetchone()[0]
        liberados = conn.execute("SELECT COUNT(*) FROM aprendizado WHERE status='SAFE'").fetchone()[0]
    finally:
        conn.close()
    return {
        "status": "OK", "blacklist_count": total, "whitelist_count": liberados,
        "model": "loaded", "dns_online": verificar_dns_local()
    }

@app.get("/api/bloqueados_full")
def api_bloqueados_full():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    # Retorna a blacklist completa para o gerenciador
    r = conn.execute("SELECT dominio FROM aprendizado WHERE status='MALWARE' ORDER BY dominio ASC").fetchall()
    conn.close()
    return [x[0] for x in r]

@app.get("/download_pihole")
def download_pihole():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    r = conn.execute("SELECT dominio FROM aprendizado WHERE status='MALWARE'").fetchall()
    conn.close()
    content = "\n".join([x[0] for x in r])
    return StreamingResponse(io.BytesIO(content.encode()), media_type="text/plain", headers={"Content-Disposition": "attachment; filename=blocklist.txt"})

@app.get("/analisar")
async def api_analisar(dominio: str):
    res = analisar_dominio(dominio)
    persistir_deteccao(dominio, res)
    registrar_evento(dominio, res["status"], res["score"], res.get("origem", ""), res.get("regra", ""), "MANUAL")
    await disparar_atualizacao()
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/bloquear_manual")
async def bloq_manual(dominio: str = Form(...)):
    salvar_db(dominio, "MALWARE", 1.0)
    with historico_lock:
        for h in historico:
            if h["dominio"] == dominio:
                h["status"], h["bloqueado"], h["score"] = "MALWARE", True, 1.0
    await disparar_atualizacao()
    return RedirectResponse("/dashboard", status_code=303)

def liberar_dominio_e_subdominios(dominio):
    dom = normalizar_dominio(dominio)
    if not dom:
        return

    # Libera o domínio informado e quaisquer subdomínios já existentes no banco.
    # A regra SAFE no domínio-pai também libera novos subdomínios desse domínio.
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        conn.execute(
            "UPDATE aprendizado SET status='SAFE', score=0.0 WHERE dominio=? OR dominio LIKE ?",
            (dom, "%." + dom),
        )
        conn.execute(
            "INSERT OR REPLACE INTO aprendizado (dominio, status, score) VALUES (?, 'SAFE', 0.0)",
            (dom,),
        )
        conn.commit()
    finally:
        conn.close()

    with historico_lock:
        for h in historico:
            hdom = normalizar_dominio(h["dominio"])
            if hdom == dom or hdom.endswith("." + dom):
                h["status"], h["bloqueado"], h["score"] = "SAFE", False, 0.0

    print(f"[LIBERADO] {dom} e subdomínios")


@app.post("/desbloquear")
async def desb_manual(dominio: str = Form(...)):
    liberar_dominio_e_subdominios(dominio)
    await disparar_atualizacao()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/liberar_preset")
async def liberar_preset(preset: str = Form(...)):
    presets = {
        "facebook": [
            "facebook.com",
            "fbcdn.net",
            "fbsbx.com",
            "messenger.com",
        ],
        "youtube": [
            "youtube.com",
            "youtu.be",
            "ytimg.com",
            "googlevideo.com",
            "youtubei.googleapis.com",
            "youtube-nocookie.com",
        ],
    }

    dominios = presets.get(preset.lower().strip())
    if not dominios:
        return RedirectResponse("/dashboard", status_code=303)

    for dom in dominios:
        liberar_dominio_e_subdominios(dom)

    await disparar_atualizacao()
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/importar_lista")
async def importar_lista(url: str = Form(...)):
    try:
        resultado = importar_lista_url(url)
        resultado["ok"] = True
        await disparar_atualizacao()
        return resultado
    except Exception as exc:
        return {"ok": False, "erro": str(exc)}


@app.get("/api/fontes_listas")
def api_fontes_listas():
    conn = conectar_db()
    try:
        rows = conn.execute(
            "SELECT url, nome, ativo, ultima_atualizacao, total_dominios, ultimo_erro FROM fontes_listas ORDER BY nome"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/estatisticas_dominios")
def api_estatisticas_dominios(limite: int = 20):
    limite = max(1, min(int(limite), 100))
    return estatisticas_dominios(limite)


@app.get("/api/stats_completa")
def stats():
    conn = conectar_db()
    try:
        total_req = conn.execute("SELECT COUNT(*) FROM historico_dns").fetchone()[0]
        total_bloq = conn.execute("SELECT COUNT(*) FROM historico_dns WHERE status='MALWARE'").fetchone()[0]
    finally:
        conn.close()

    return {
        "total_req": int(total_req),
        "total_bloq": int(total_bloq),
        "historico": obter_historico(10),
        "top_dominios": estatisticas_dominios(8),
        "dns_online": verificar_dns_local(),
        "tempo_real": estatisticas_tempo_real(10),
        "bloqueios_recentes": estatisticas_bloqueios_recentes(10),
        "tipos_dns": estatisticas_tipos_dns(10, 5),
    }

# --- RESOLVER DNS ---
class MyResolver(BaseResolver):
    def resolve(self, request, handler):
        domain = normalizar_dominio(str(request.q.qname))

        # Consulta interna usada apenas pelo indicador real de status do dashboard.
        if domain == HEALTHCHECK_DOMAIN:
            reply = request.reply()
            reply.header.rcode = RCODE.NXDOMAIN
            return reply

        res = analisar_dominio(domain)

        persistir_deteccao(domain, res)
        try:
            tipo_consulta = QTYPE.get(request.q.qtype, str(request.q.qtype))
        except Exception:
            tipo_consulta = str(request.q.qtype)
        registrar_evento(
            domain, res["status"], res["score"], res.get("origem", ""),
            res.get("regra", ""), tipo_consulta
        )

        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(disparar_atualizacao())
            loop.close()
        except Exception as exc:
            print(f"[AVISO] Falha ao atualizar dashboard: {exc}")

        # Bloqueio consistente para A, AAAA, CNAME e outros tipos de consulta.
        if res["status"] == "MALWARE":
            regra = res.get("regra", domain)
            print(f"[BLOQUEADO] {domain} | regra={regra} | origem={res.get('origem')}")
            reply = request.reply()
            reply.header.rcode = RCODE.NXDOMAIN
            return reply

        # Encaminha consultas permitidas ao DNS upstream.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(DNS_TIMEOUT)
        try:
            sock.sendto(request.pack(), UPSTREAM_DNS)
            data, _ = sock.recvfrom(65535)
            return DNSRecord.parse(data)
        except (socket.timeout, OSError, ValueError) as exc:
            print(f"[DNS ERRO] {domain}: {exc}")
            reply = request.reply()
            reply.header.rcode = RCODE.SERVFAIL
            return reply
        finally:
            sock.close()

if __name__ == "__main__":
    def run_dns():
        try:
            print(f"[DNS] Banco em uso: {DB_FILE}")
            print(f"[DNS] Upstream: {UPSTREAM_DNS[0]}:{UPSTREAM_DNS[1]}")
            print("[DNS] Iniciando servidor em 127.0.0.1:53 (UDP)...")
            DNSServer(MyResolver(), port=53, address="127.0.0.1", tcp=False).start()
        except PermissionError:
            print("[ERRO DNS] Sem permissão para abrir a porta 53. Execute o terminal como Administrador.")
        except OSError as exc:
            print(f"[ERRO DNS] Não foi possível abrir a porta 53: {exc}")
        except Exception as exc:
            print(f"[ERRO DNS] Falha inesperada no servidor DNS: {exc}")

    threading.Thread(target=run_dns, daemon=True).start()
    threading.Thread(target=loop_atualizacao_listas, daemon=True).start()

    import uvicorn
    print("[WEB] Dashboard: http://127.0.0.1:8000/dashboard")
    uvicorn.run(app, host="127.0.0.1", port=8000)
