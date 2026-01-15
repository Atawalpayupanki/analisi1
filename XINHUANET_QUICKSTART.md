# Guía Rápida: Usar Feeds de Xinhuanet (Sin Docker)

## ✅ Estado Actual

Los feeds RSS de Xinhuanet están **listos para usar** sin necesidad de Docker.

## 📁 Feeds Disponibles

Los siguientes archivos XML están actualizados en `xinhuanet-rss/feeds/`:

- ✅ `xinhua_china.xml` - Noticias Nacionales
- ✅ `xinhua_world.xml` - Noticias Internacionales  
- ✅ `xinhua_finance.xml` - Finanzas
- ✅ `xinhua_tech.xml` - Tecnología
- ✅ `xinhua_sports.xml` - Deportes
- ✅ `xinhua_ent.xml` - Entretenimiento

## 🚀 Cómo Usar

### Opción 1: Desde la GUI (Recomendado)

1. Abre la aplicación:
   ```powershell
   python src/gui.py
   ```

2. Ve a la pestaña **"Feeds Chinos"**

3. Haz clic en **"Procesar Feeds Chinos"**

4. La aplicación usará automáticamente los feeds estáticos de Xinhuanet

### Opción 2: Desde la Línea de Comandos

```powershell
python src/main.py --modo async
```

## 🔄 Actualizar Feeds

Para obtener las noticias más recientes, ejecuta:

```powershell
python update_xinhua_feeds.py
```

**Recomendación:** Actualiza los feeds diariamente para tener noticias frescas.

## 📝 Notas

- **No necesitas Docker** - Los feeds estáticos funcionan perfectamente
- **Actualización manual** - Ejecuta `update_xinhua_feeds.py` cuando quieras noticias nuevas
- **Configuración automática** - La app ya está configurada para usar estos feeds

## ❓ Solución de Problemas

### Si no aparecen noticias:

1. Verifica que los archivos XML existan en `xinhuanet-rss/feeds/`
2. Actualiza los feeds: `python update_xinhua_feeds.py`
3. Revisa que `config/rss_feeds_zh.json` tenga las rutas correctas

### Si quieres usar RSSHub en el futuro:

1. Instala Docker Desktop
2. Ejecuta: `python manage_rsshub.py start`
3. Los feeds dinámicos se usarán automáticamente

---

**¡Listo para usar!** 🎉
