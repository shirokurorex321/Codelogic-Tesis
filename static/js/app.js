// ─── CodeLogic IUP — App JS ─────────────────

// ── CSRF ──────────────────────────────────────
// Envuelve window.fetch para adjuntar el token CSRF en toda petición que
// modifique estado. Así las llamadas de editor.html, test.html y scale.html
// funcionan sin cambiarlas una por una.
(() => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) return;
    const token = meta.getAttribute('content');

    const SAFE = ['GET', 'HEAD', 'OPTIONS', 'TRACE'];
    const originalFetch = window.fetch;

    window.fetch = function (input, init) {
        init = init || {};
        const method = (init.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();

        // Solo peticiones que cambian estado y que van a nuestro propio origen
        if (!SAFE.includes(method)) {
            const url = (input instanceof Request) ? input.url : String(input);
            let sameOrigin = true;
            try {
                sameOrigin = new URL(url, window.location.href).origin === window.location.origin;
            } catch (_) { /* URL relativa → mismo origen */ }

            if (sameOrigin) {
                const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
                if (!headers.has('X-CSRFToken')) headers.set('X-CSRFToken', token);
                init = { ...init, headers };
            }
        }
        return originalFetch.call(this, input, init);
    };
})();

// ── Mensajes flash ────────────────────────────
// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
});

// ── Qué sigue después de superar un ejercicio ─────────────────
// Lo usan el editor y los ejercicios de leer y de diagrama. `sig` lo calcula
// el servidor (siguiente_paso en app.py): el siguiente ejercicio pendiente
// del tema o, si ya no queda ninguno, la lección del tema siguiente.
function htmlSiguientePaso(sig, urlTema) {
    const esc = t => String(t == null ? '' : t)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    if (!sig) {
        return '<a href="' + esc(urlTema) + '" class="btn btn-primary btn-sm siguiente-paso">Volver al tema →</a>';
    }
    if (sig.tipo === 'ejercicio') {
        return '<a href="' + esc(sig.url) + '" class="btn btn-primary btn-sm siguiente-paso">'
            + esc(sig.texto) + ' →</a>';
    }
    const titulo = sig.tipo === 'curso_terminado'
        ? '🎓 ¡Terminaste todos los temas!'
        : '🏁 ¡Terminaste el tema «' + esc(sig.tema) + '»!';
    return '<div class="tema-terminado"><strong>' + titulo + '</strong>'
        + '<a href="' + esc(sig.url) + '" class="btn btn-primary btn-sm">' + esc(sig.texto) + ' →</a></div>';
}
