# -*- coding: utf-8 -*-
"""Envío de correo de CodeLogic.

Usa la cuenta institucional (@itp.edu.co vía Google Workspace). Los mensajes
van de un dominio a sí mismo, que es tráfico interno y llega a bandeja de
entrada en lugar de spam.

El envío se hace en un hilo aparte: si el servidor de correo tarda, el
estudiante no se queda esperando en la pantalla de registro.
"""
import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage
from email.utils import formataddr

from config import Config

logger = logging.getLogger(__name__)

TIMEOUT = 30


def _enviar_sync(destino: str, asunto: str, texto: str, html: str = None) -> bool:
    """Envía de verdad. Devuelve True si el servidor lo aceptó."""
    if not Config.EMAIL_VERIFICATION_ENABLED:
        logger.warning("SMTP no configurado: no se envía correo a %s", destino)
        return False

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = formataddr((Config.SMTP_FROM_NAME, Config.SMTP_USER))
    msg["To"] = destino
    msg.set_content(texto)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        ctx = ssl.create_default_context()
        if int(Config.SMTP_PORT) == 465:
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT,
                                  timeout=TIMEOUT, context=ctx) as s:
                s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                s.send_message(msg)
        else:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=TIMEOUT) as s:
                s.starttls(context=ctx)
                s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                s.send_message(msg)
        logger.info("Correo enviado a %s: %s", destino, asunto)
        return True
    except Exception:
        logger.exception("Fallo al enviar correo a %s", destino)
        return False


def enviar(destino: str, asunto: str, texto: str, html: str = None,
           en_segundo_plano: bool = True) -> bool:
    """Encola el envío. Con en_segundo_plano=False espera y devuelve el
    resultado real (útil para pruebas)."""
    if not en_segundo_plano:
        return _enviar_sync(destino, asunto, texto, html)
    threading.Thread(
        target=_enviar_sync, args=(destino, asunto, texto, html), daemon=True
    ).start()
    return True


def correo_verificacion(nombre: str, destino: str, enlace: str, horas: int):
    """Arma y envía el correo de verificación de cuenta."""
    asunto = "Confirma tu cuenta en CodeLogic IUP"

    texto = f"""Hola {nombre},

Gracias por registrarte en CodeLogic, la plataforma de aprendizaje de
programación de la Institución Universitaria del Putumayo.

Para activar tu cuenta, abre este enlace:

{enlace}

El enlace vence en {horas} horas.

Si no fuiste tú quien se registró, ignora este mensaje: sin confirmar, la
cuenta no se activa.

— CodeLogic IUP
"""

    html = f"""<!doctype html>
<html lang="es">
<body style="margin:0;padding:24px;background:#0f1420;font-family:'Segoe UI',Arial,sans-serif;color:#e8edf7;">
  <div style="max-width:520px;margin:0 auto;background:#161d2e;border-radius:14px;padding:32px;border:1px solid rgba(255,255,255,.08);">
    <p style="font-size:22px;font-weight:700;margin:0 0 4px;">⟨/⟩ CodeLogic <span style="opacity:.6;font-size:15px;">IUP</span></p>
    <p style="opacity:.65;margin:0 0 24px;font-size:13px;">Institución Universitaria del Putumayo</p>

    <p style="font-size:16px;margin:0 0 12px;">Hola <strong>{nombre}</strong>,</p>
    <p style="line-height:1.6;margin:0 0 24px;opacity:.9;">
      Gracias por registrarte. Solo falta un paso: confirma que este correo es tuyo
      para activar tu cuenta.
    </p>

    <p style="text-align:center;margin:0 0 24px;">
      <a href="{enlace}"
         style="display:inline-block;background:#4f7cff;color:#fff;text-decoration:none;
                padding:14px 32px;border-radius:10px;font-weight:600;font-size:15px;">
        Confirmar mi cuenta
      </a>
    </p>

    <p style="font-size:13px;opacity:.6;line-height:1.6;margin:0 0 8px;">
      Si el botón no funciona, copia y pega esta dirección en tu navegador:
    </p>
    <p style="font-size:12px;opacity:.5;word-break:break-all;margin:0 0 24px;">{enlace}</p>

    <hr style="border:none;border-top:1px solid rgba(255,255,255,.08);margin:24px 0;">
    <p style="font-size:12px;opacity:.55;line-height:1.6;margin:0;">
      El enlace vence en {horas} horas.<br>
      Si no fuiste tú, ignora este mensaje: sin confirmar, la cuenta no se activa.
    </p>
  </div>
</body>
</html>"""

    return enviar(destino, asunto, texto, html)


def correo_restablecer(nombre: str, destino: str, enlace: str, minutos: int):
    """Correo con el enlace para elegir una contraseña nueva."""
    asunto = "Restablece tu contraseña de CodeLogic IUP"

    texto = f"""Hola {nombre},

Recibimos una solicitud para restablecer la contraseña de tu cuenta en
CodeLogic.

Abre este enlace para elegir una contraseña nueva:

{enlace}

El enlace vence en {minutos} minutos y solo puede usarse una vez.

Si no fuiste tú, ignora este mensaje: tu contraseña actual sigue funcionando
y nadie puede cambiarla sin abrir este enlace.

— CodeLogic IUP
"""

    html = f"""<!doctype html>
<html lang="es">
<body style="margin:0;padding:24px;background:#0f1420;font-family:'Segoe UI',Arial,sans-serif;color:#e8edf7;">
  <div style="max-width:520px;margin:0 auto;background:#161d2e;border-radius:14px;padding:32px;border:1px solid rgba(255,255,255,.08);">
    <p style="font-size:22px;font-weight:700;margin:0 0 4px;">&lt;/&gt; CodeLogic <span style="opacity:.6;font-size:15px;">IUP</span></p>
    <p style="opacity:.65;margin:0 0 24px;font-size:13px;">Institución Universitaria del Putumayo</p>

    <p style="font-size:16px;margin:0 0 12px;">Hola <strong>{nombre}</strong>,</p>
    <p style="line-height:1.6;margin:0 0 24px;opacity:.9;">
      Recibimos una solicitud para restablecer tu contraseña. Pulsa el botón
      para elegir una nueva.
    </p>

    <p style="text-align:center;margin:0 0 24px;">
      <a href="{enlace}"
         style="display:inline-block;background:#4f7cff;color:#fff;text-decoration:none;
                padding:14px 32px;border-radius:10px;font-weight:600;font-size:15px;">
        Elegir contraseña nueva
      </a>
    </p>

    <p style="font-size:13px;opacity:.6;line-height:1.6;margin:0 0 8px;">
      Si el botón no funciona, copia esta dirección en tu navegador:
    </p>
    <p style="font-size:12px;opacity:.5;word-break:break-all;margin:0 0 24px;">{enlace}</p>

    <hr style="border:none;border-top:1px solid rgba(255,255,255,.08);margin:24px 0;">
    <p style="font-size:12px;opacity:.55;line-height:1.6;margin:0;">
      El enlace vence en {minutos} minutos y solo sirve una vez.<br>
      Si no fuiste tú, ignora este mensaje: tu contraseña actual sigue activa.
    </p>
  </div>
</body>
</html>"""

    return enviar(destino, asunto, texto, html)
