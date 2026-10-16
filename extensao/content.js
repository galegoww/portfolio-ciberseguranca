function limparBanners() {
    const hostname = window.location.hostname;

    if (hostname.includes("youtube.com") || hostname.includes("google.com")) {
        return;
    }

    const palavrasSuspeitas = ["DOWNLOAD", "BAIXAR AGORA", "PRONTO PARA JOGAR", "INSTALAR", "PLAY NOW", "CLICK AQUI", "ABRIR", "TESTE GRATUITO"];

    function deveIgnorarElemento(el) {
        if (el.closest('header, nav, footer, form, iframe, textarea, svg')) return true;
        if (el.matches('[role="navigation"], [role="banner"], [role="complementary"], [aria-hidden="true"]')) return true;
        return false;
    }

    function temTextoAd(texto) {
        return palavrasSuspeitas.some(p => texto.includes(p));
    }

    function pareceAnuncio(el) {
        const alvo = [el.id, el.className, el.getAttribute('role'), el.getAttribute('aria-label')]
            .filter(Boolean)
            .join(' ')
            .toUpperCase();
        const estilo = window.getComputedStyle(el);
        const seletorSugereAd = /(AD|ADS|ADVERTISEMENT|BANNER|POPUP|PROMO|SPONSOR)/.test(alvo);
        const layoutSuspeito = estilo.position === 'fixed' || estilo.position === 'sticky';
        return seletorSugereAd || layoutSuspeito;
    }

    document.querySelectorAll('a, button, aside, [role="dialog"], [class*="banner"], [class*="popup"], [class*="promo"], [id*="banner"], [id*="popup"], [id*="promo"]').forEach(el => {
        if (deveIgnorarElemento(el)) return;
        if (!pareceAnuncio(el)) return;

        const texto = el.innerText ? el.innerText.trim().toUpperCase() : "";
        if (!texto || !temTextoAd(texto)) return;

        const largura = el.offsetWidth;
        const altura = el.offsetHeight;
        if (largura < 80 || largura > 800 || altura < 20 || altura > 400) return;

        console.log("🛡️ DNS AI SHIELD: Removendo elemento suspeito:", texto);
        el.style.setProperty('display', 'none', 'important');
    });
}

const observer = new MutationObserver(() => limparBanners());

observer.observe(document.documentElement, {
    childList: true,
    subtree: true
});

window.addEventListener('load', limparBanners);
setTimeout(limparBanners, 2000);
