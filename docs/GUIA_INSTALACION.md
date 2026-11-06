# Guía: preparar tu computadora (Windows)

Los bots que operan **tienen que correr en tu computadora** (o en un servidor en un país permitido).
Binance bloquea su API desde los servidores de la nube donde trabaja Claude.

## 1. Instalar Python (una sola vez)
1. Entra a https://www.python.org/downloads/ y descarga Python 3.12 o más nuevo.
2. Al instalar, **marca la casilla "Add python.exe to PATH"** y da clic en *Install Now*.

## 2. Bajar el proyecto
- **Con GitHub Desktop:** File → Clone repository → elige `RomeroEG44/trading-bots` → Clone.
- Para traer cambios nuevos que haga Claude: botón **Fetch origin** y luego **Pull origin**.

## 3. Instalar lo que necesita el proyecto (una sola vez)
Abre la carpeta del proyecto, escribe `cmd` en la barra de direcciones del explorador y presiona Enter. En la
ventana negra escribe:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Cada vez que abras una ventana nueva para usar los bots, primero corre `.venv\Scripts\activate`.

## 4. Crear las claves del Testnet (dinero de prueba)
1. Entra a https://testnet.binance.vision y da clic en **Log In with GitHub**.
2. Da clic en **Generate HMAC_SHA256 Key**, ponle un nombre (por ejemplo `bots`) y genera la clave.
3. Copia la **API Key** y la **Secret Key**. La Secret solo se muestra una vez.

## 5. Guardar las claves en tu computadora
1. En la carpeta del proyecto, copia el archivo `.env.example` y renombra la copia a `.env`.
2. Ábrelo con el Bloc de notas y pega tus claves:
   ```
   MODO=testnet
   BINANCE_API_KEY=lo_que_copiaste
   BINANCE_API_SECRET=lo_que_copiaste
   ```
3. Guarda el archivo. **Nunca compartas este archivo ni lo pegues en el chat.** GitHub lo ignora automáticamente.

## 6. Probar la conexión (no compra ni vende nada)
```
python -m tradingbots.verificar_conexion
```
Si ves `Conexión exitosa` y tus saldos de prueba, la Fase 0 está terminada. Si sale un error, copia el mensaje
(nunca las claves) y pégaselo a Claude.

## Extra: correr el backtest tú mismo
```
python -m tradingbots.backtest
python -m tradingbots.backtest --config config/real.yaml --dias 365
```
El reporte queda en la carpeta `reports/`.

---

# Fase 2: poner los bots a trabajar (Testnet)

## 7. Actualizar el proyecto
En GitHub Desktop: **Fetch origin** y luego **Pull origin**. Después, en la ventana negra (con `.venv\Scripts\activate`):
```
pip install -r requirements.txt
```

## 8. Conectar Telegram (para que el supervisor te escriba)
1. En Telegram busca **@BotFather** (tiene una palomita azul) y escríbele `/newbot`.
2. Ponle un nombre (por ejemplo `Supervisor Edgar`) y un usuario que termine en `bot` (por ejemplo `edgar_supervisor_bot`).
3. BotFather te da un **token** (algo como `123456:ABC-...`). Pégalo en `.env` como `TELEGRAM_BOT_TOKEN=...`.
4. Abre el chat con tu bot nuevo y mándale cualquier mensaje (por ejemplo `hola`).
5. En el navegador abre `https://api.telegram.org/botTU_TOKEN/getUpdates` (cambia `TU_TOKEN` por el token).
   Busca `"chat":{"id":` y copia ese número. Pégalo en `.env` como `TELEGRAM_CHAT_ID=...`.

Solo ese chat (el tuyo) puede darle órdenes a los bots; los mensajes de cualquier otra persona se ignoran.

## 9. Arrancar
- **Doble clic en `iniciar_bots.bat`**. Se abre la ventana negra (déjala abierta) y el panel en el navegador.
- O desde la ventana negra: `python -m tradingbots.motor`
- Panel: **http://localhost:8000**. Solo se puede abrir desde tu computadora.
- Para apagar: en la ventana negra presiona `Ctrl + C`. Al volver a arrancar, cada bot recuerda dónde se quedó.

## 10. Comandos de Telegram
| Comando | Qué hace |
|---|---|
| `/estado` | Cómo van los bots ahora mismo |
| `/reporte` | Resumen de las últimas 24 h (también llega solo cada día a las 8 a.m.) |
| `/pausar` | Pausa las compras de todos. Las ventas de protección (stop-loss) siguen funcionando |
| `/pausar dca_btc` | Pausa solo ese bot |
| `/reanudar` o `/reanudar dca_btc` | Reanuda |
| `/detener_todo` | Freno de emergencia: solo se reanuda con `/reanudar` |

## Cosas importantes
- **Si la computadora se suspende o se apaga, los bots se detienen.** En Windows: Configuración → Sistema →
  Inicio/apagado y suspensión → "Suspender" en **Nunca** mientras estén corriendo.
- El panel muestra **"✅ Funcionando"** si el motor está vivo y **"❌ Sin señal"** si dejó de responder.
- **El Testnet de Binance se reinicia de vez en cuando** (borra los saldos de prueba). Si empiezan a salir errores de
  "Saldo insuficiente", borra el archivo `data\bots_testnet.sqlite` y vuelve a arrancar.
- **Modo papel:** si pones `MODO=papel` en `.env`, todo funciona igual pero simulado, sin claves de Binance.
- El bot Tendencia usa velas **diarias**: decide **una vez al día** (a las 6 p.m. hora de México, que es la medianoche UTC).
  Es normal que pase días sin operar. El DCA compra una vez por semana.
