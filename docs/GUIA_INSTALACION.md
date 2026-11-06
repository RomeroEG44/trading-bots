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

# Fase 2: los 6 bots en paralelo en el Testnet

## 7. Actualizar el proyecto
En GitHub Desktop: **Fetch origin** y luego **Pull origin**. Después, en la ventana negra (con `.venv\Scripts\activate`):
```
pip install -r requirements.txt
```
Si antes probaste la versión anterior, borra el archivo `data\bots_testnet.sqlite` para empezar de cero.

## 8. Arrancar
- **Doble clic en `iniciar_bots.bat`**. Se abre la ventana negra (déjala abierta) y el panel en el navegador.
- O desde la ventana negra: `python -m tradingbots.motor`
- Panel: **http://localhost:8000** (solo desde tu computadora). Se actualiza cada 3 segundos.
- Para apagar: `Ctrl + C` en la ventana negra. Al volver a arrancar, cada bot y el Master recuerdan dónde se quedaron.

No tienes que confirmar nada: los bots, el Master y el Supervisor deciden solos.

## 9. Qué vas a ver en el panel
| Sección | Qué muestra |
|---|---|
| Arriba | Modo (TESTNET), estado del Supervisor, "En vivo" (si el motor responde) y el botón de emergencia |
| Tarjetas | Valor total, resultado, ganancia realizada, operaciones y % de acierto global |
| Bots en paralelo | Los 6 bots ordenados por resultado: estado según el Master, tamaño, aciertos, factor de beneficio, peor caída, comisiones y señal actual |
| Detalle del bot | Clic en un bot: gráfica de precio con sus compras ▲ y ventas ▼, su análisis en este momento y lo que el Master opina de él |
| Feedback | Todo lo que el Master y el Supervisor deciden, en vivo |
| Operaciones | Cada compra y venta de todos los bots con su motivo |

## Cosas importantes
- **Saldo del Testnet:** los 6 bots usan 400 USDT cada uno (2,400 en total). Si tu cuenta de Testnet tiene menos,
  baja `presupuesto_usdt` en `config/testnet.yaml`.
- **Si la computadora se suspende, los bots se detienen.** En Windows: Configuración → Sistema → Inicio/apagado y suspensión
  → "Suspender" en **Nunca**.
- **El Testnet de Binance se reinicia de vez en cuando** (borra los saldos). Si aparecen errores de "Saldo insuficiente",
  borra `data\bots_testnet.sqlite` y vuelve a arrancar.
- **Modo papel:** con `MODO=papel` en `.env` todo funciona igual pero simulado, sin claves.
- **Ajustar bots o reglas del Master:** todo está en `config/testnet.yaml`. Pídele a Claude que lo cambie.
