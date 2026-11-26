#!/bin/bash
# ═══════════════════════════════════════════════════════════
# CodeLogic IUP — Respaldo diario de la base de datos
# Los datos del pilotaje (sep–oct 2026) NO se pueden regenerar.
# ═══════════════════════════════════════════════════════════
set -euo pipefail

ENV_FILE=/opt/codelogic/app/.env
# Movido al disco de respaldos el 15/08/2026. Estaba en el SSD del sistema,
# que es la misma unidad que aloja la base de datos: un fallo de ese disco se
# habria llevado por delante los datos y sus copias a la vez.
DEST=/mnt/respaldos/codelogic
RETENCION_DIAS=30

# Credenciales desde el .env, sin exponerlas en la línea de comandos
DB_USER=$(grep -E '^DB_USER=' "$ENV_FILE" | cut -d= -f2-)
DB_PASSWORD=$(grep -E '^DB_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)
DB_NAME=$(grep -E '^DB_NAME=' "$ENV_FILE" | cut -d= -f2-)

STAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVO="$DEST/codelogic-${STAMP}.sql.gz"

# --defaults-file por stdin evita que la contraseña salga en `ps`
mariadb-dump \
    --defaults-file=<(printf '[client]\nuser=%s\npassword=%s\n' "$DB_USER" "$DB_PASSWORD") \
    --single-transaction --quick --routines --events \
    "$DB_NAME" | gzip -9 > "$ARCHIVO"

# Un respaldo vacío es peor que ninguno: avisa en vez de fingir que funcionó
TAM=$(stat -c%s "$ARCHIVO")
if [ "$TAM" -lt 1024 ]; then
    echo "ERROR: el respaldo pesa ${TAM} bytes — algo falló" >&2
    rm -f "$ARCHIVO"
    exit 1
fi

# Verificar que el gzip está íntegro y contiene la tabla de usuarios.
# Se cuenta con `grep -c` en vez de `grep -q`: con -q, grep sale al primer
# acierto, zcat recibe SIGPIPE al seguir escribiendo y `set -o pipefail` da
# por fallida la tuberia entera — descartando un respaldo que estaba bien.
# Hoy no salta porque la tabla `users` queda casi al final del volcado y a
# zcat le sobra poco por escribir, pero es cuestion de que crezcan las
# tablas anteriores. Con -c, grep lee hasta el final y no hay SIGPIPE.
if [ "$(zcat "$ARCHIVO" | grep -c "CREATE TABLE \`users\`")" -eq 0 ]; then
    echo "ERROR: el respaldo no contiene la tabla users — descartado" >&2
    rm -f "$ARCHIVO"
    exit 1
fi

chmod 640 "$ARCHIVO"
echo "OK respaldo: $ARCHIVO ($(numfmt --to=iec "$TAM"))"

# Retención
BORRADOS=$(find "$DEST" -name 'codelogic-*.sql.gz' -mtime +${RETENCION_DIAS} -print -delete | wc -l)
[ "$BORRADOS" -gt 0 ] && echo "   purgados $BORRADOS respaldo(s) de más de ${RETENCION_DIAS} días"

echo "   total almacenado: $(du -sh "$DEST" | cut -f1) en $(find "$DEST" -name '*.sql.gz' | wc -l) archivo(s)"
