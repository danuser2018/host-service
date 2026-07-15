# Especificación de Requisitos

# Host Service

**Versión:** 1.0
**Estado:** Propuesta

---

# 1. Introducción

## 1.1 Objetivo

El **Host Service** es un nuevo componente del ecosistema Nova cuya misión es encapsular todas las operaciones que requieren interacción directa con el sistema operativo del usuario.

El servicio actuará como una **capa de abstracción del host (Host Abstraction Layer)** ofreciendo una API REST estable que permita al resto de servicios y plugins realizar operaciones sobre el sistema sin conocer los detalles de implementación del sistema operativo.

El Host Service constituye la única puerta de entrada para realizar acciones sobre el host.

---

## 1.2 Motivación

Actualmente Nova dispone de servicios especializados para distintas áreas:

* system-service (información sobre Nova)
* identity-service (identidad del usuario)
* weather-service (meteorología)
* mail-watchdog (correo)

Sin embargo, todavía no existe un servicio responsable del acceso al sistema operativo.

La creación del Host Service permite:

* aislar completamente las operaciones del host;
* evitar que plugins ejecuten comandos del sistema directamente;
* facilitar la evolución futura del sistema;
* centralizar aspectos de seguridad;
* proporcionar una API estable e independiente de la implementación.

---

# 2. Alcance

La primera versión del Host Service implementará exclusivamente el control del volumen del sistema.

Las futuras versiones podrán incorporar:

* brillo de pantalla;
* energía;
* bluetooth;
* notificaciones;
* aplicaciones;
* ventanas;
* dispositivos USB;
* estado del sistema.

---

# 3. Arquitectura

## 3.1 Posición dentro del ecosistema

El Host Service será un servicio **nativo del host**.

No estará dockerizado.

Se ejecutará mediante:

```
systemd --user
```

Su ejecución tendrá exactamente los mismos permisos que el usuario que haya iniciado sesión.

No deberá requerir privilegios administrativos.

---

## 3.2 Responsabilidad

El servicio únicamente conoce el sistema operativo.

No conoce:

* Nova
* Plugins
* Conversaciones
* LLM
* Orchestrator

Su única responsabilidad consiste en ejecutar operaciones sobre el host y devolver el resultado.

---

## 3.3 Principios de diseño

El servicio deberá cumplir los siguientes principios:

* Responsabilidad única.
* Stateless.
* API REST.
* Idempotencia cuando sea posible.
* Independencia del consumidor.
* Sin conocimiento del dominio Nova.
* Fácilmente testeable.

---

# 4. Requisitos Funcionales

## RF-001

El sistema deberá exponer una API REST accesible desde el resto de servicios del ecosistema.

---

## RF-002

El sistema deberá permitir consultar el volumen actual.

---

## RF-003

El sistema deberá permitir incrementar el volumen.

---

## RF-004

El sistema deberá permitir disminuir el volumen.

---

## RF-005

El sistema deberá permitir establecer un volumen absoluto.

---

## RF-006

El sistema deberá permitir silenciar el sistema.

---

## RF-007

El sistema deberá permitir restaurar el sonido.

---

## RF-008

El sistema deberá permitir alternar entre mute y unmute.

---

## RF-009

Todas las operaciones deberán devolver el estado actualizado del sistema.

---

## RF-010

El servicio deberá devolver errores HTTP normalizados.

---

# 5. Requisitos No Funcionales

## RNF-001 Rendimiento

Las operaciones deberán completarse en menos de 100 ms en condiciones normales.

---

## RNF-002 Stateless

El servicio no almacenará estado propio.

Toda la información se obtendrá del sistema operativo.

---

## RNF-003 Seguridad

El servicio nunca ejecutará operaciones con privilegios superiores al usuario que lo ejecuta.

No utilizará sudo.

---

## RNF-004 Compatibilidad

La implementación deberá ser compatible con:

* Linux
* PulseAudio
* PipeWire

---

## RNF-005 Disponibilidad

El servicio deberá ejecutarse como servicio de usuario mediante systemd.

---

## RNF-006 Observabilidad

Todas las operaciones deberán registrarse mediante logging estructurado.

---

## RNF-007 API estable

La API deberá mantenerse compatible entre versiones mayores.

---

# 6. Restricciones

El servicio:

* no conocerá Nova;
* no accederá a bases de datos;
* no accederá al sistema de plugins;
* no mantendrá sesiones;
* no implementará lógica conversacional.

---

# 7. Casos de uso

### Consultar volumen

Usuario:

> ¿Qué volumen tengo?

Plugin:

```
GET /v1/audio/volume
```

---

### Subir volumen

Usuario:

> Sube el volumen.

Plugin:

```
POST /v1/audio/volume/up
```

---

### Bajar volumen

Usuario:

> Baja el volumen.

Plugin:

```
POST /v1/audio/volume/down
```

---

### Silenciar

Usuario:

> Silencia el ordenador.

Plugin:

```
POST /v1/audio/mute
```

---

# Anexo A

# API REST propuesta

## Obtener volumen

```
GET /v1/audio/volume
```

Respuesta

```json
{
  "volume": 43,
  "muted": false
}
```

---

## Subir volumen

```
POST /v1/audio/volume/up
```

Body

```json
{
  "step": 5
}
```

Respuesta

```json
{
  "volume": 48,
  "muted": false
}
```

---

## Bajar volumen

```
POST /v1/audio/volume/down
```

Body

```json
{
  "step": 5
}
```

---

## Establecer volumen

```
POST /v1/audio/volume/set
```

Body

```json
{
  "volume": 80
}
```

---

## Mute

```
POST /v1/audio/mute
```

---

## Unmute

```
POST /v1/audio/unmute
```

---

## Toggle mute

```
POST /v1/audio/toggle-mute
```

---

## Health

```
GET /health
```

---

# Anexo B

# Implementación Linux

Se utilizará exclusivamente la utilidad:

```
pactl
```

Compatible tanto con:

* PulseAudio
* PipeWire

Comandos principales:

Consultar volumen

```bash
pactl get-sink-volume @DEFAULT_SINK@
```

Consultar mute

```bash
pactl get-sink-mute @DEFAULT_SINK@
```

Incrementar volumen

```bash
pactl set-sink-volume @DEFAULT_SINK@ +5%
```

Reducir volumen

```bash
pactl set-sink-volume @DEFAULT_SINK@ -5%
```

Establecer volumen

```bash
pactl set-sink-volume @DEFAULT_SINK@ 80%
```

Silenciar

```bash
pactl set-sink-mute @DEFAULT_SINK@ 1
```

Activar sonido

```bash
pactl set-sink-mute @DEFAULT_SINK@ 0
```

Alternar mute

```bash
pactl set-sink-mute @DEFAULT_SINK@ toggle
```

---

# Anexo C

# Instalación

El servicio se instalará como servicio de usuario.

Unidad systemd:

```
~/.config/systemd/user/host-service.service
```

Gestión:

```bash
systemctl --user daemon-reload
```

```bash
systemctl --user enable host-service
```

```bash
systemctl --user start host-service
```

Estado:

```bash
systemctl --user status host-service
```

Logs:

```bash
journalctl --user -u host-service -f
```

---

# Anexo D

# Integración con Nova

Se añade un nuevo servicio al plano Host.

## Antes

```
Host

- mic-daemon
- speaker-watchdog
- hid-daemon
```

## Después

```
Host

- mic-daemon
- speaker-watchdog
- hid-daemon
- host-service
```

El resto de servicios accederán al Host Service mediante HTTP REST.

Ejemplo:

```
Volume Plugin

↓

host-service

↓

pactl
```

Ningún plugin ejecutará comandos del sistema directamente.

---

# Anexo E

# Evolución prevista

El Host Service se diseñará para admitir nuevas capacidades sin modificar su arquitectura.

Posibles módulos futuros:

## Audio

* volumen
* mute
* selección de dispositivo

## Pantalla

* brillo
* temperatura de color

## Energía

* bloqueo
* suspensión
* hibernación
* apagado

## Bluetooth

* consulta de dispositivos
* conexión
* desconexión

## Notificaciones

* notificaciones del escritorio

## Aplicaciones

* abrir aplicaciones
* cerrar aplicaciones

## Ventanas

* enfocar
* minimizar
* maximizar

## Sistema

* batería
* CPU
* memoria
* discos
* temperatura

---

# Anexo F

# Consideraciones de seguridad

Aunque la primera versión únicamente implementa operaciones de bajo riesgo (control del volumen), el servicio deberá diseñarse pensando en futuras capacidades con mayor impacto sobre el sistema.

Se recomienda clasificar cada operación según su nivel de privilegio (por ejemplo: bajo, medio, alto o crítico) y reservar un punto de extensión para integrar posteriormente un **Security Manager** encargado de autorizar operaciones sensibles. De este modo, la API pública del Host Service podrá mantenerse estable mientras evolucionan las políticas de seguridad del ecosistema Nova.