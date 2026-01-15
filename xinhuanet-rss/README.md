# Xinhuanet RSS Feed Generator

Este proyecto proporciona una solución completa para generar feeds RSS actualizados de Xinhuanet (新华网) en chino simplificado usando RSSHub.

## 📋 Contenido

- [Instalación](#instalación)
- [Configuración](#configuración)
- [URLs de Feeds Disponibles](#urls-de-feeds-disponibles)
- [Uso](#uso)
- [Mantenimiento Automático](#mantenimiento-automático)
- [Soluciones Alternativas](#soluciones-alternativas)

## 🚀 Instalación

### Opción 1: Docker (Recomendado)

Docker es la forma más sencilla y confiable de ejecutar RSSHub.

#### Requisitos previos
- Docker Desktop para Windows ([Descargar aquí](https://www.docker.com/products/docker-desktop))

#### Pasos de instalación

1. **Instalar Docker Desktop**
   - Descarga e instala Docker Desktop
   - Reinicia tu computadora si es necesario
   - Verifica la instalación:
   ```powershell
   docker --version
   ```

2. **Descargar y ejecutar RSSHub**
   ```powershell
   docker pull diygod/rsshub
   docker run -d --name rsshub -p 1200:1200 diygod/rsshub
   ```

3. **Verificar que funciona**
   - Abre tu navegador en: `http://localhost:1200`
   - Deberías ver la página de bienvenida de RSSHub

### Opción 2: Instalación Local (Node.js)

Si prefieres ejecutar RSSHub sin Docker:

#### Requisitos previos
- Node.js 18+ ([Descargar aquí](https://nodejs.org/))
- Git ([Descargar aquí](https://git-scm.com/))

#### Pasos de instalación

1. **Clonar el repositorio de RSSHub**
   ```powershell
   cd C:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss
   git clone https://github.com/DIYgod/RSSHub.git
   cd RSSHub
   ```

2. **Instalar dependencias**
   ```powershell
   npm install --production
   ```

3. **Iniciar RSSHub**
   ```powershell
   npm start
   ```

4. **Verificar que funciona**
   - Abre tu navegador en: `http://localhost:1200`

## ⚙️ Configuración

### Variables de entorno (Opcional)

Crea un archivo `.env` en el directorio de RSSHub para configuraciones avanzadas:

```env
# Puerto del servidor (por defecto: 1200)
PORT=1200

# Cache (mejora el rendimiento)
CACHE_TYPE=memory
CACHE_EXPIRE=300

# Límite de solicitudes (para evitar bloqueos)
REQUEST_RETRY=3
REQUEST_TIMEOUT=30000

# Proxy (si necesitas evitar restricciones geográficas)
# PROXY_URI=http://proxy-server:port
```

## 📡 URLs de Feeds Disponibles

Una vez que RSSHub esté ejecutándose en `http://localhost:1200`, puedes acceder a los siguientes feeds de Xinhuanet:

### Categorías Principales

| Categoría | Descripción | URL del Feed |
|-----------|-------------|--------------|
| **国内 (Nacional)** | Noticias nacionales de China | `http://localhost:1200/xinhua/china` |
| **国际 (Internacional)** | Noticias internacionales | `http://localhost:1200/xinhua/world` |
| **财经 (Finanzas)** | Noticias económicas y financieras | `http://localhost:1200/xinhua/finance` |
| **科技 (Tecnología)** | Noticias de ciencia y tecnología | `http://localhost:1200/xinhua/tech` |
| **体育 (Deportes)** | Noticias deportivas | `http://localhost:1200/xinhua/sports` |
| **娱乐 (Entretenimiento)** | Noticias de entretenimiento | `http://localhost:1200/xinhua/ent` |
| **军事 (Militar)** | Noticias militares | `http://localhost:1200/xinhua/mil` |
| **港澳 (Hong Kong/Macao)** | Noticias de Hong Kong y Macao | `http://localhost:1200/xinhua/gangao` |
| **台湾 (Taiwán)** | Noticias de Taiwán | `http://localhost:1200/xinhua/tw` |

### Feeds Especializados

```
# Últimas noticias
http://localhost:1200/xinhua/latest

# Noticias en inglés
http://localhost:1200/xinhua/english

# Comentarios y opiniones
http://localhost:1200/xinhua/comments
```

## 📱 Uso

### 1. Agregar feeds a tu lector RSS

#### FeedMe (Android)
1. Abre FeedMe
2. Toca el botón "+"
3. Selecciona "Agregar feed"
4. Pega la URL del feed (ej: `http://localhost:1200/xinhua/china`)
5. Toca "Agregar"

#### Feedly
1. Abre Feedly
2. Haz clic en "Add Content"
3. Pega la URL del feed
4. Haz clic en "Follow"

> **Nota**: Si accedes desde otro dispositivo en tu red local, reemplaza `localhost` con la IP de tu computadora (ej: `http://192.168.1.100:1200/xinhua/china`)

### 2. Verificar que los feeds funcionan

Abre cualquier URL de feed en tu navegador. Deberías ver el XML del feed RSS con las últimas noticias.

## 🔄 Mantenimiento Automático

### Opción 1: Iniciar RSSHub automáticamente con Docker

**Configurar inicio automático:**
```powershell
docker update --restart unless-stopped rsshub
```

Ahora RSSHub se iniciará automáticamente cuando arranque Docker Desktop.

### Opción 2: Crear un servicio de Windows (Node.js)

Si usas la instalación local, puedes usar NSSM (Non-Sucking Service Manager):

1. **Descargar NSSM**
   - Descarga desde: https://nssm.cc/download
   - Extrae `nssm.exe` a una carpeta accesible

2. **Instalar RSSHub como servicio**
   ```powershell
   # Ejecutar como Administrador
   nssm install RSSHub "C:\Program Files\nodejs\node.exe" "C:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss\RSSHub\lib\index.js"
   nssm start RSSHub
   ```

### Opción 3: Script de inicio automático

Crea un archivo `start-rsshub.bat` en la carpeta de inicio de Windows:

```batch
@echo off
cd C:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss\RSSHub
start /min npm start
```

Coloca este archivo en: `C:\Users\pauta\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

## 🔧 Soluciones Alternativas

### Si RSSHub no funciona para alguna sección

#### 1. Feed43 (Servicio web gratuito)

Feed43 convierte cualquier página web en RSS mediante reglas de extracción:

1. Ve a https://feed43.com
2. Crea una cuenta gratuita
3. Ingresa la URL de la sección de Xinhuanet
4. Define las reglas de extracción usando patrones
5. Genera el feed RSS

**Ejemplo para noticias nacionales:**
- URL: `http://www.news.cn/politics/`
- Patrón de título: `<h3>{%}</h3>`
- Patrón de enlace: `<a href="{%}">`

#### 2. RSS Bridge

Alternativa a RSSHub con diferentes routers:

```powershell
docker pull rssbridge/rss-bridge
docker run -d -p 3000:80 rssbridge/rss-bridge
```

Accede en: `http://localhost:3000`

#### 3. Scraping personalizado con Python

Si necesitas control total, puedes crear tu propio scraper. Ver archivo `custom_scraper.py` en este directorio.

## 🆘 Solución de Problemas

### RSSHub no inicia
- Verifica que el puerto 1200 no esté en uso: `netstat -ano | findstr :1200`
- Revisa los logs de Docker: `docker logs rsshub`

### Feeds vacíos o con errores
- Xinhuanet puede haber cambiado su estructura HTML
- Verifica la URL original en el navegador
- Considera usar una solución alternativa

### No puedo acceder desde otro dispositivo
- Verifica que tu firewall permita conexiones en el puerto 1200
- Usa la IP local de tu PC en lugar de `localhost`
- Asegúrate de que ambos dispositivos estén en la misma red

## 📚 Recursos Adicionales

- [Documentación oficial de RSSHub](https://docs.rsshub.app/)
- [Lista completa de routers de RSSHub](https://docs.rsshub.app/routes/traditional-media)
- [Xinhuanet oficial](http://www.news.cn/)

## 📝 Notas

- Los feeds se actualizan automáticamente cada vez que tu lector RSS los consulta
- RSSHub cachea los resultados para mejorar el rendimiento
- Si Xinhuanet bloquea las solicitudes, considera usar un proxy o VPN
