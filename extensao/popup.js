const API_HOSTS = ["http://127.0.0.1:8000", "http://localhost:8000"];

const statusEl = document.getElementById("server-status");
const btnBloq = document.getElementById("btnBloq");
const btnAnal = document.getElementById("btnAnal");
let servidorOnline = false;

function atualizarEstadoServidor(online, mensagem, cor) {
    servidorOnline = online;
    statusEl.innerText = mensagem;
    statusEl.style.color = cor;
    btnBloq.disabled = !online;
    btnAnal.disabled = !online;
    btnBloq.style.opacity = online ? "1" : "0.5";
    btnAnal.style.opacity = online ? "1" : "0.5";
}

async function requestHost(path, options = {}) {
    for (const host of API_HOSTS) {
        try {
            const res = await fetch(`${host}${path}`, options);
            if (res.ok) return { host, res };
        } catch (_) {
            continue;
        }
    }
    throw new Error("Servidor não disponível");
}

async function getActiveHost() {
    const { host } = await requestHost("/api/status");
    return host;
}

async function carregar() {
    const ul = document.getElementById("lista");
    atualizarEstadoServidor(false, "Servidor: verificando...", "#94a3b8");

    try {
        const { res: statusRes } = await requestHost("/api/status");
        const statusData = await statusRes.json();

        atualizarEstadoServidor(true, `Servidor: ${statusData.status} — ${statusData.blacklist_count} domínios`, "#22c55e");

        const { res: r } = await requestHost("/api/bloqueados");
        const d = await r.json();
        ul.innerHTML = d.bloqueados.map(s => `<li>${s}</li>`).join("");
        chrome.runtime.sendMessage({action: "reload"});
    } catch (e) {
        atualizarEstadoServidor(false, "Servidor offline", "#f87171");
        ul.innerHTML = "<li>Python Offline</li>";
    }
}

const urlInput = document.getElementById("url");

function obterDominio() {
    const dom = urlInput.value.trim();
    if (!dom) {
        alert("Digite um domínio para continuar.");
        urlInput.focus();
        return null;
    }
    return dom;
}

btnBloq.addEventListener("click", async () => {
    if (!servidorOnline) {
        alert("Servidor offline. Aguarde até que ele esteja disponível.");
        return;
    }

    const dom = obterDominio();
    if (!dom) return;

    try {
        const fd = new FormData();
        fd.append("dominio", dom);
        const { res } = await requestHost("/bloquear_manual", { method: "POST", body: fd });
        if (!res.ok) throw new Error("Falha ao bloquear domínio");
        carregar();
    } catch (error) {
        alert("Erro ao bloquear o domínio. Verifique se o servidor está online.");
    }
});

btnAnal.addEventListener("click", async () => {
    if (!servidorOnline) {
        alert("Servidor offline. Aguarde até que ele esteja disponível.");
        return;
    }

    const dom = obterDominio();
    if (!dom) return;

    try {
        const host = await getActiveHost();
        window.open(`${host}/analisar?dominio=${encodeURIComponent(dom)}`, "_blank");
    } catch (error) {
        alert("Servidor offline. Aguarde até que ele esteja disponível.");
    }
});

carregar();