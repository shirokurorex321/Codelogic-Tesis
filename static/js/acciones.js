/* Despachador de acciones declarativas.
 *
 * Las plantillas tenian 43 manejadores escritos dentro del HTML
 * (onclick="convertir()"), y eso obligaba a permitir 'unsafe-inline' en la
 * CSP: con esa puerta abierta, cualquier XSS que se cuele puede ejecutar lo
 * que quiera. Ahora el HTML solo DECLARA que hacer y este fichero, que se
 * carga como recurso propio, lo conecta.
 *
 *   data-accion="convertir"              -> llama a convertir() al pulsar
 *   data-accion="switchTab" data-args='["python"]'  -> switchTab('python')
 *   data-cambio="cambiarTipo"            -> al cambiar un select
 *   data-confirmar="¿Seguro?"            -> pregunta antes de enviar el form
 *   data-sin-enviar                      -> el form no se envia (lo maneja JS)
 *   data-cerrar                          -> quita el elemento contenedor
 *
 * Se usa delegacion en document para que funcione tambien con lo que se
 * pinta despues, y para no tener que enganchar nada a mano.
 */
(function () {
    "use strict";

    function argumentos(el) {
        const crudo = el.getAttribute("data-args");
        if (!crudo) return [];
        try {
            const v = JSON.parse(crudo);
            return Array.isArray(v) ? v : [v];
        } catch (e) {
            console.warn("data-args no es JSON válido:", crudo);
            return [];
        }
    }

    function invocar(nombre, el, evento) {
        const fn = window[nombre];
        if (typeof fn !== "function") {
            console.warn("La acción «" + nombre + "» no existe.");
            return;
        }
        // El evento va SIEMPRE como ultimo argumento: las funciones que no lo
        // necesitan simplemente lo ignoran, y las que si -como la que captura
        // el tabulador en el editor- lo reciben sin tener que declararlo aqui.
        try { fn.apply(el, argumentos(el).concat([evento])); }
        catch (e) { console.error("Fallo en la acción «" + nombre + "»:", e); }
    }

    document.addEventListener("click", function (ev) {
        const cerrar = ev.target.closest("[data-cerrar]");
        if (cerrar) {
            const padre = cerrar.parentElement;
            if (padre) padre.remove();
            return;
        }
        const el = ev.target.closest("[data-accion]");
        if (el) invocar(el.getAttribute("data-accion"), el, ev);
    });

    document.addEventListener("change", function (ev) {
        const el = ev.target.closest("[data-cambio]");
        if (el) invocar(el.getAttribute("data-cambio"), el, ev);
    });

    document.addEventListener("input", function (ev) {
        const el = ev.target.closest("[data-entrada]");
        if (el) invocar(el.getAttribute("data-entrada"), el, ev);
    });

    document.addEventListener("keydown", function (ev) {
        const el = ev.target.closest("[data-tecla]");
        if (el) invocar(el.getAttribute("data-tecla"), el, ev);
    });

    document.addEventListener("submit", function (ev) {
        const form = ev.target;
        if (form.hasAttribute("data-sin-enviar")) { ev.preventDefault(); return; }
        const msg = form.getAttribute("data-confirmar");
        if (msg && !window.confirm(msg)) ev.preventDefault();
    }, true);
})();
