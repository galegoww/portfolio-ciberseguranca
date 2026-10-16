const API_HOSTS = ["http://127.0.0.1:8000", "http://localhost:8000"];

async function requestHost(path) {
    for (const host of API_HOSTS) {
        try {
            const res = await fetch(`${host}${path}`);
            if (res.ok) return { host, res };
        } catch (_) { continue; }
    }
    throw new Error("Servidor Offline");
}

async function sincronizar() {
    try {
        const { res } = await requestHost("/api/bloqueados");
        const data = await res.json();
        
        if (!data.bloqueados) return;

        const rules = data.bloqueados.map((dom, i) => ({
            id: i + 1,
            priority: 1,
            action: { type: "block" },
            condition: { urlFilter: dom, resourceTypes: ["main_frame", "script", "image"] }
        }));

        const oldRules = await chrome.declarativeNetRequest.getDynamicRules();
        await chrome.declarativeNetRequest.updateDynamicRules({
            removeRuleIds: oldRules.map(r => r.id),
            addRules: rules.slice(0, 5000) // Limite do Chrome
        });
        
        console.log("🛡️ Shield Online: " + data.bloqueados.length + " sites.");
    } catch (e) {
        console.log("⚠️ Servidor não detectado.");
    }
}

chrome.runtime.onInstalled.addListener(sincronizar);
chrome.runtime.onStartup.addListener(sincronizar);
setInterval(sincronizar, 60000); // Sincroniza a cada 1 minuto