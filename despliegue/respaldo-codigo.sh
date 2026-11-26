#!/bin/bash
# ═══════════════════════════════════════════════════════════
# CodeLogic IUP — Respaldo diario del código
#
# Complementa a backup.sh, que solo guarda la base de datos. Sin el
# código, un volcado de la base no sirve para volver a levantar nada.
#
# Deja tres cosas en /mnt/respaldos (disco distinto al del sistema):
#   1. el historial de git, empujado al repositorio espejo
#   2. un .tar.gz plano, por si el repositorio se corrompe
#   3. el .env, que git excluye a proposito por llevar las claves
# ═══════════════════════════════════════════════════════════
set -euo pipefail

APP=/opt/codelogic/app
DEST=/mnt/respaldos/codelogic-codigo
ESPEJO="$DEST/repositorio.git"
RETENCION=14   # numero de .tar.gz que se conservan

cd "$APP"

# ── 1. Confirmar los cambios que haya sueltos ──────────────────────
# Se trabaja editando ficheros en caliente, no con ramas; si algo quedo
# sin confirmar, este es el punto donde entra al historial.
if [ -n "$(git status --porcelain)" ]; then
    # Comprobacion de seguridad: que el .gitignore no se haya roto y
    # este a punto de entrar un secreto al historial. Si pasa, se para.
    if git status --porcelain | grep -qE '^\?\?.*\.env$|^A.*\.env$|^M.*\.env$'; then
        echo "ERROR: el .env esta a punto de entrar a git — revisa .gitignore" >&2
        exit 1
    fi
    git add -A
    git commit -q -m "Cambios automaticos del $(date +%d/%m/%Y)

Confirmado por el respaldo diario, no a mano. Si esta linea aparece
mucho es que se esta editando en caliente sin confirmar despues."
    echo "OK confirmados los cambios sueltos"
else
    echo "   sin cambios que confirmar"
fi

# ── 2. Empujar al espejo ───────────────────────────────────────────
git push --quiet respaldo principal
echo "OK historial empujado al espejo ($(git rev-list --count principal) confirmacion/es)"

# ── 3. Copia plana ─────────────────────────────────────────────────
STAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVO="$DEST/codelogic-codigo-${STAMP}.tar.gz"

# Las exclusiones van ANTES del operando: puestas despues, tar avisa de
# que "no tienen efecto" y las ignora en silencio.
tar czf "$ARCHIVO" \
    --exclude=venv --exclude=__pycache__ --exclude='*.pyc' \
    --exclude=instance --exclude='*.antes-*' --exclude='*.sql*' \
    -C /opt/codelogic app

# Un archivo corrupto es peor que ninguno: se comprueba de verdad que
# abre y que lleva dentro lo que tiene que llevar.
if ! gzip -t "$ARCHIVO" 2>/dev/null; then
    echo "ERROR: el .tar.gz salio corrupto — descartado" >&2
    rm -f "$ARCHIVO"; exit 1
fi
# El listado se guarda antes de filtrarlo, sin tuberia, a proposito:
# `tar tzf ... | grep -q` parece correcto pero destruye respaldos buenos.
# grep -q sale al primer acierto, tar recibe SIGPIPE al seguir escribiendo,
# y `set -o pipefail` da la tuberia entera por fallida. El resultado es que
# se descarta un archivo que estaba perfecto.
LISTA=$(tar tzf "$ARCHIVO")
if ! grep -q '^app/app.py$' <<<"$LISTA"; then
    echo "ERROR: el .tar.gz no contiene app.py — descartado" >&2
    rm -f "$ARCHIVO"; exit 1
fi

chmod 640 "$ARCHIVO"
echo "OK copia plana: $ARCHIVO ($(numfmt --to=iec "$(stat -c%s "$ARCHIVO")"))"

# ── 4. Los secretos, que git no guarda ─────────────────────────────
install -d -m 700 "$DEST/secretos"
cp -p "$APP/.env" "$DEST/secretos/.env"
chmod 600 "$DEST/secretos/.env"
echo "OK .env copiado ($(grep -cE '^[A-Z_]+=' "$DEST/secretos/.env") claves)"

# ── 5. Retencion ───────────────────────────────────────────────────
# Se cuentan y se borran las mas viejas por numero, no por fecha: si el
# equipo pasa un mes apagado, por fecha se borrarian todas de golpe.
SOBRAN=$(ls -1t "$DEST"/codelogic-codigo-*.tar.gz 2>/dev/null | tail -n +$((RETENCION + 1)) || true)
if [ -n "$SOBRAN" ]; then
    echo "$SOBRAN" | xargs -r rm -f
    echo "   purgadas $(echo "$SOBRAN" | wc -l) copia(s) antiguas"
fi

echo "   total: $(du -sh "$DEST" | cut -f1) en $DEST"
