# Guía Rápida de Inicio

## 🚀 Inicio Rápido (Método más fácil)

### Usando Docker (Recomendado)

1. **Instala Docker Desktop**
   - Descarga: https://www.docker.com/products/docker-desktop
   - Instala y reinicia tu PC si es necesario

2. **Ejecuta el script de inicio**
   - Haz doble clic en `start-rsshub.bat`
   - Espera a que RSSHub se inicie (unos 10-15 segundos)

3. **Verifica que funciona**
   - Abre tu navegador en: http://localhost:1200
   - Deberías ver la página de RSSHub

4. **Agrega los feeds a tu lector RSS**
   - Copia las URLs de `feeds.json`
   - Pégalas en tu lector RSS favorito (FeedMe, Feedly, etc.)

## 📱 URLs de Feeds Principales

```
Nacional:        http://localhost:1200/xinhua/china
Internacional:   http://localhost:1200/xinhua/world
Finanzas:        http://localhost:1200/xinhua/finance
Tecnología:      http://localhost:1200/xinhua/tech
Deportes:        http://localhost:1200/xinhua/sports
Entretenimiento: http://localhost:1200/xinhua/ent
```

## 🔧 Comandos Útiles

### Iniciar RSSHub
```powershell
docker start rsshub-xinhuanet
```

### Detener RSSHub
```powershell
docker stop rsshub-xinhuanet
```

### Ver logs
```powershell
docker logs rsshub-xinhuanet
```

### Reiniciar RSSHub
```powershell
docker restart rsshub-xinhuanet
```

### Eliminar contenedor
```powershell
docker stop rsshub-xinhuanet
docker rm rsshub-xinhuanet
```

## 📖 Documentación Completa

Para instrucciones detalladas, consulta `README.md`

## 🆘 Problemas Comunes

### "Docker no está instalado"
- Instala Docker Desktop desde el enlace arriba
- Reinicia tu PC después de la instalación

### "Puerto 1200 ya está en uso"
- Detén el proceso que usa el puerto 1200
- O cambia el puerto en `docker-compose.yml`

### "No puedo acceder desde mi teléfono"
- Reemplaza `localhost` con la IP de tu PC
- Ejemplo: `http://192.168.1.100:1200/xinhua/china`
- Verifica que tu firewall permita conexiones en el puerto 1200

### "Los feeds están vacíos"
- Espera unos segundos y recarga
- Verifica que RSSHub esté ejecutándose: `docker ps`
- Revisa los logs: `docker logs rsshub-xinhuanet`

## 🔄 Alternativas

Si RSSHub no funciona para ti:

1. **Scraper personalizado**: Usa `custom_scraper.py`
   ```powershell
   python custom_scraper.py
   ```

2. **Feed43**: Servicio web gratuito
   - https://feed43.com

3. **RSS Bridge**: Alternativa a RSSHub
   - Ver README.md para instrucciones
