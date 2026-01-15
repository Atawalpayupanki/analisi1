# ⚠️ IMPORTANTE: Actualización sobre RSSHub y Xinhuanet

## Problema Descubierto

Después de instalar y probar RSSHub, he descubierto que **los routers de Xinhuanet (`/xinhua/china`, `/xinhua/world`, etc.) NO están disponibles** en la versión actual de RSSHub.

![RSSHub funcionando](file:///C:/Users/pauta/.gemini/antigravity/brain/a1d6e5a5-606b-4d31-840e-76a8e6244195/rsshub_homepage_1767034554330.png)

![Error al intentar acceder al feed de Xinhua](file:///C:/Users/pauta/.gemini/antigravity/brain/a1d6e5a5-606b-4d31-840e-76a8e6244195/xinhua_feed_error_1767034562899.png)

## ✅ Solución: Scraper Personalizado en Python

Dado que RSSHub no soporta Xinhuanet actualmente, la mejor opción es usar el **scraper personalizado** que he creado.

---

## 🚀 Guía de Uso del Scraper Personalizado

### Paso 1: Instalar Dependencias

```powershell
cd c:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss
pip install -r requirements.txt
```

### Paso 2: Ejecutar el Scraper

#### Opción A: Generar un feed específico

```powershell
python custom_scraper.py
```

Esto generará `xinhua_china.xml` con las últimas noticias nacionales.

#### Opción B: Generar todos los feeds

Edita `custom_scraper.py` y descomenta la línea:

```python
# En la función main(), cambia:
rss_xml = scraper.generate_rss('china', 'xinhua_china.xml')

# Por:
scraper.generate_all_feeds('./feeds')
```

Esto creará feeds para todas las categorías en la carpeta `feeds/`.

### Paso 3: Servir los Feeds Localmente

Para que los feeds sean accesibles desde tu lector RSS, necesitas un servidor web local:

```powershell
# Opción 1: Servidor HTTP simple de Python
cd c:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss
python -m http.server 8000
```

Ahora los feeds estarán disponibles en:
- `http://localhost:8000/xinhua_china.xml`
- `http://localhost:8000/feeds/xinhua_world.xml`
- etc.

### Paso 4: Automatizar la Actualización

Para mantener los feeds actualizados, crea un script que ejecute el scraper periódicamente.

**Crear `update_feeds.bat`:**

```batch
@echo off
cd c:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss
python custom_scraper.py
timeout /t 3600 /nobreak
goto :loop
```

Esto actualizará los feeds cada hora.

---

## 📡 URLs de Feeds Disponibles

Una vez que tengas el servidor HTTP ejecutándose:

| Categoría | URL del Feed |
|-----------|--------------|
| Nacional (国内) | `http://localhost:8000/feeds/xinhua_china.xml` |
| Internacional (国际) | `http://localhost:8000/feeds/xinhua_world.xml` |
| Finanzas (财经) | `http://localhost:8000/feeds/xinhua_finance.xml` |
| Tecnología (科技) | `http://localhost:8000/feeds/xinhua_tech.xml` |
| Deportes (体育) | `http://localhost:8000/feeds/xinhua_sports.xml` |
| Entretenimiento (娱乐) | `http://localhost:8000/feeds/xinhua_ent.xml` |

---

## 🔄 Alternativa: Crear un Router Personalizado para RSSHub

Si prefieres usar RSSHub, puedes crear tu propio router personalizado:

### 1. Clonar RSSHub

```powershell
cd c:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\xinhuanet-rss
git clone https://github.com/DIYgod/RSSHub.git
cd RSSHub
```

### 2. Crear el Router de Xinhuanet

Crea el archivo `lib/routes/xinhua/china.ts`:

```typescript
import { Route } from '@/types';
import cache from '@/utils/cache';
import got from '@/utils/got';
import { load } from 'cheerio';

export const route: Route = {
    path: '/china',
    categories: ['traditional-media'],
    example: '/xinhua/china',
    parameters: {},
    features: {
        requireConfig: false,
        requirePuppeteer: false,
        antiCrawler: false,
        supportBT: false,
        supportPodcast: false,
        supportScihub: false,
    },
    radar: [
        {
            source: ['news.cn/politics'],
        },
    ],
    name: '国内新闻',
    maintainers: ['custom'],
    handler,
};

async function handler() {
    const baseUrl = 'http://www.news.cn';
    const url = `${baseUrl}/politics/`;

    const response = await got(url);
    const $ = load(response.data);

    const items = $('a')
        .toArray()
        .map((item) => {
            const $item = $(item);
            const title = $item.text().trim();
            const link = $item.attr('href');

            if (!link || !title || title.length < 10) {
                return null;
            }

            const fullLink = link.startsWith('http') ? link : baseUrl + link;

            return {
                title,
                link: fullLink,
                description: title,
                pubDate: new Date().toUTCString(),
            };
        })
        .filter((item) => item !== null)
        .slice(0, 20);

    return {
        title: '新华网 - 国内新闻',
        link: url,
        item: items,
    };
}
```

### 3. Registrar el Router

Crea `lib/routes/xinhua/namespace.ts`:

```typescript
import type { Namespace } from '@/types';

export const namespace: Namespace = {
    name: '新华网',
    url: 'news.cn',
};
```

### 4. Compilar y Ejecutar

```powershell
npm install
npm run build
npm start
```

Ahora el feed estará disponible en: `http://localhost:1200/xinhua/china`

---

## 📊 Comparación de Soluciones

| Solución | Ventajas | Desventajas |
|----------|----------|-------------|
| **Scraper Python** | ✓ Fácil de usar<br>✓ Control total<br>✓ No requiere Node.js | ✗ Requiere servidor HTTP<br>✗ Actualización manual |
| **Router RSSHub Personalizado** | ✓ Integración con RSSHub<br>✓ Cache automático<br>✓ Actualización automática | ✗ Requiere conocimientos de TypeScript<br>✗ Más complejo de configurar |
| **Servicios Externos** | ✓ Sin mantenimiento<br>✓ Siempre disponible | ✗ Dependencia externa<br>✗ Posibles límites de uso |

---

## 🎯 Recomendación

Para empezar rápidamente, usa el **scraper personalizado en Python**:

1. Instala las dependencias: `pip install -r requirements.txt`
2. Ejecuta el scraper: `python custom_scraper.py`
3. Inicia el servidor HTTP: `python -m http.server 8000`
4. Agrega `http://localhost:8000/xinhua_china.xml` a tu lector RSS

Si necesitas una solución más robusta a largo plazo, considera crear el router personalizado para RSSHub.

---

## 🆘 Soporte

Si tienes problemas con el scraper, verifica:

1. **Dependencias instaladas**: `pip list | findstr requests`
2. **Conexión a Xinhuanet**: Abre `http://www.news.cn/politics/` en tu navegador
3. **Permisos de escritura**: Asegúrate de poder crear archivos en el directorio

Para más ayuda, consulta los archivos:
- [custom_scraper.py](file:///c:/Users/pauta/Desktop/pau/bachiller/phipatia/analitzador/xinhuanet-rss/custom_scraper.py)
- [README.md](file:///c:/Users/pauta/Desktop/pau/bachiller/phipatia/analitzador/xinhuanet-rss/README.md)
