"""Mensajes entre el supervisor y Edgar por Telegram.

Seguridad: solo se aceptan comandos que vengan del chat de Edgar (TELEGRAM_CHAT_ID).
Si no hay token configurado, los mensajes solo se muestran en la consola.
"""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)


class Notificador:
    def __init__(self, token: str = "", chat_id: str = "", sesion=None):
        self.token = token
        self.chat_id = str(chat_id)
        self.activo = bool(token and chat_id)
        self.sesion = sesion or requests.Session()
        self._offset: int | None = None
        if self.activo:
            self._descartar_pendientes()

    def _url(self, metodo: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{metodo}"

    def enviar(self, texto: str) -> None:
        log.info("[mensaje] %s", texto.replace("\n", " | "))
        if not self.activo:
            return
        try:
            self.sesion.post(self._url("sendMessage"), json={
                "chat_id": self.chat_id, "text": texto[:4000], "parse_mode": "HTML", "disable_web_page_preview": True,
            }, timeout=15).raise_for_status()
        except Exception as e:  # un fallo de Telegram nunca debe detener a los bots
            log.warning("No se pudo enviar a Telegram: %s", e)

    def leer_comandos(self) -> list[str]:
        """Devuelve los comandos nuevos (p. ej. '/estado') enviados por Edgar."""
        if not self.activo:
            return []
        try:
            params = {"timeout": 0, "allowed_updates": '["message"]'}
            if self._offset is not None:
                params["offset"] = self._offset
            r = self.sesion.get(self._url("getUpdates"), params=params, timeout=15)
            r.raise_for_status()
            comandos = []
            for u in r.json().get("result", []):
                self._offset = u["update_id"] + 1
                msg = u.get("message") or {}
                if str(msg.get("chat", {}).get("id")) != self.chat_id:
                    log.warning("Comando ignorado de un chat desconocido: %s", msg.get("chat", {}).get("id"))
                    continue
                texto = (msg.get("text") or "").strip()
                if texto.startswith("/"):
                    comandos.append(texto)
            return comandos
        except Exception as e:
            log.warning("No se pudieron leer comandos de Telegram: %s", e)
            return []

    def _descartar_pendientes(self) -> None:
        """Al arrancar, ignora comandos viejos para no ejecutar algo que Edgar mandó hace horas."""
        try:
            r = self.sesion.get(self._url("getUpdates"), params={"timeout": 0, "offset": -1}, timeout=15)
            res = r.json().get("result", [])
            if res:
                self._offset = res[-1]["update_id"] + 1
        except Exception as e:
            log.warning("Telegram no responde al arrancar: %s", e)
