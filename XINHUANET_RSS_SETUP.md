# Configuración de Xinhuanet RSS

Este documento explica cómo usar los feeds RSS de Xinhuanet integrados en la aplicación.

## 📋 Descripción General

La aplicación ahora soporta dos fuentes de feeds RSS de Xinhuanet:

1. **RSSHub (Dinámico)** - Servicio Docker que genera feeds en tiempo real
2. **Feeds Estáticos** - Archivos XML generados por scraper personalizado (fallback)

## 🚀 Inicio Rápido

### Opción 1: Usar RSSHub (Recomendado)

RSSHub proporciona feeds actualizados en tiempo real desde Xinhuanet.

**Iniciar RSSHub:**
```powershell
python manage_rsshub.py start
```

**Verificar estado:**
```powershell
python manage_rsshub.py status
```

**Probar feeds:**
```powershell
python manage_rsshub.py test
```

**Detener RSSHub:**
```powershell
python manage_rsshub.py stop
```

### Opción 2: Usar Feeds Estáticos

Si no puedes usar Docker o RSSHub no está disponible, puedes usar feeds estáticos.

**Actualizar feeds estáticos:**
```powershell
python update_xinhua_feeds.py
```

Los feeds se guardan en: `xinhuanet-rss/feeds/`

## 📰 Feeds Disponibles

### RSSHub (localhost:1200)

| Categoría | URL |
|-----------|-----|
| Nacional | http://localhost:1200/xinhua/china |
| Internacional | http://localhost:1200/xinhua/world |
| Finanzas | http://localhost:1200/xinhua/finance |
| Tecnología | http://localhost:1200/xinhua/tech |
| Deportes | http://localhost:1200/xinhua/sports |
| Entretenimiento | http://localhost:1200/xinhua/ent |
| Militar | http://localhost:1200/xinhua/mil |
| Hong Kong/Macao | http://localhost:1200/xinhua/gangao |
| Taiwán | http://localhost:1200/xinhua/tw |
| Últimas Noticias | http://localhost:1200/xinhua/latest |

### Feeds Estáticos

Los feeds estáticos se encuentran en `xinhuanet-rss/feeds/`:
- `xinhua_china.xml` - Noticias nacionales
- `xinhua_world.xml` - Noticias internacionales
- `xinhua_finance.xml` - Finanzas
- `xinhua_tech.xml` - Tecnología
- `xinhua_sports.xml` - Deportes
- `xinhua_ent.xml` - Entretenimiento

## 🔧 Configuración

Los feeds están configurados en `config/rss_feeds_zh.json`:

```json
{
    "feeds": [
        {
            "nombre": "Xinhua 新华网 (RSSHub Local)",
            "urls": [
                "http://localhost:1200/xinhua/china",
                "http://localhost:1200/xinhua/world",
                ...
            ]
        },
        {
            "nombre": "Xinhua 新华网 (Static Feeds)",
            "urls": [
                "file:///c:/Users/pauta/.../xinhua_china.xml",
                ...
            ]
        }
    ]
}
```

## 🐳 Requisitos para RSSHub

- **Docker Desktop** instalado y corriendo
- **Puerto 1200** disponible

### Instalar Docker Desktop

1. Descarga desde: https://www.docker.com/products/docker-desktop
2. Instala y reinicia tu PC
3. Abre Docker Desktop
4. Verifica con: `docker --version`

## 🔄 Uso en la Aplicación

### Desde la GUI

1. Abre la aplicación: `python src/gui.py`
2. Ve a la pestaña **"Feeds Chinos"**
3. Haz clic en **"Procesar Feeds Chinos"**
4. La aplicación intentará usar RSSHub primero
5. Si RSSHub no está disponible, usará los feeds estáticos

### Desde la Línea de Comandos

```powershell
# Procesar feeds chinos
python src/main.py --modo async

# O modo síncrono
python src/main.py --modo sync
```

## 📊 Monitoreo

### Ver logs de RSSHub

```powershell
cd xinhuanet-rss
docker-compose logs -f
```

### Ver estado del contenedor

```powershell
docker ps -a --filter name=rsshub-xinhuanet
```

## 🛠️ Solución de Problemas

### RSSHub no inicia

**Problema:** `docker-compose up -d` falla

**Soluciones:**
1. Verifica que Docker Desktop esté corriendo
2. Verifica que el puerto 1200 esté libre: `netstat -ano | findstr :1200`
3. Revisa los logs: `docker-compose logs`

### Feeds no se cargan

**Problema:** La aplicación no puede descargar feeds

**Soluciones:**
1. Verifica que RSSHub esté corriendo: `python manage_rsshub.py status`
2. Prueba los feeds manualmente: `python manage_rsshub.py test`
3. Usa feeds estáticos como alternativa: `python update_xinhua_feeds.py`

### Feeds estáticos desactualizados

**Problema:** Los feeds estáticos tienen noticias antiguas

**Solución:**
```powershell
python update_xinhua_feeds.py
```

Se recomienda actualizar los feeds estáticos regularmente (ej: diariamente).

## 📅 Mantenimiento

### Actualización Automática (Opcional)

Puedes programar una tarea en Windows para actualizar los feeds automáticamente:

1. Abre **Programador de tareas**
2. Crea una nueva tarea
3. Acción: `python update_xinhua_feeds.py`
4. Frecuencia: Diaria a las 6:00 AM

### Limpieza

Para limpiar el caché de RSSHub:

```powershell
cd xinhuanet-rss
docker-compose down -v
docker-compose up -d
```

## 🌐 Acceso desde Otros Dispositivos

Si quieres acceder a RSSHub desde otros dispositivos en tu red:

1. Encuentra tu IP local: `ipconfig`
2. Reemplaza `localhost` con tu IP en las URLs
3. Ejemplo: `http://192.168.1.100:1200/xinhua/china`

## 📝 Notas

- **RSSHub** cachea los resultados por 5 minutos por defecto
- Los **feeds estáticos** deben actualizarse manualmente
- La aplicación usa RSSHub como fuente principal y feeds estáticos como fallback
- Todos los feeds están en **chino simplificado**

## 🔗 Referencias

- [RSSHub Documentation](https://docs.rsshub.app/)
- [Xinhuanet Official](http://www.xinhuanet.com/)
- [Docker Documentation](https://docs.docker.com/)
