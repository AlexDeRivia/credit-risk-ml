# Demo de riesgo crediticio

Prototipo académico de portfolio, inspirado en un caso bancario. No está afiliado a Interbank ni sirve para tomar decisiones crediticias reales. El modelo fue entrenado con un dataset de aprobación de préstamos externo al banco. Ese dataset incluye un puntaje CIBIL y plazos en años; la interfaz presenta importes en unidades referenciales porque el modelo no está calibrado para clientes peruanos. **Solo deben ingresarse datos ficticios.**

## Funciones

- Evaluación individual con un Random Forest experimental.
- Evaluación de hasta 10 casos de un Excel `.xlsx` de máximo 1 MB.
- Historial y exportación de resultados dentro de una sesión de una hora.

No hay cuentas ni base de datos de solicitantes. El historial se guarda en una cookie firmada del visitante; esta firma evita cambios no autorizados, pero no cifra su contenido. Por ello la interfaz exige identificadores y alias ficticios.

## Ejecución local

Se recomienda Python 3.11. Crea un entorno virtual nuevo; el antiguo directorio `venv/` pertenece a otra máquina y no debe utilizarse.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Configura `DJANGO_DEBUG=true` y ejecuta:

```sh
python manage.py check
python manage.py test
python manage.py runserver
```

En PowerShell puedes usar `$env:DJANGO_DEBUG='true'`. Para generar la clave de producción después de instalar Django: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. Guárdala como secreto en la plataforma, fuera del repositorio.

La plantilla para los lotes está en `static/plantilla_lote.xlsx`. Sus columnas se validan por nombre y orden. Las opciones `educativo` son `tecnico` o `secundaria`; las de `autonomo` son `si` o `no`.

## Despliegue público

La imagen `Dockerfile` ejecuta Gunicorn y sirve archivos estáticos con WhiteNoise. Configura estas variables en la plataforma antes del arranque:

```text
DJANGO_SECRET_KEY=<valor aleatorio secreto de al menos 50 caracteres>
DJANGO_ALLOWED_HOSTS=<dominio público sin esquema>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<dominio público>
DJANGO_DEBUG=false
```

La plataforma debe terminar HTTPS y reenviar al contenedor por una red privada. Si su proxy elimina los encabezados `X-Forwarded-Proto` aportados por clientes y coloca el propio, configura `DJANGO_TRUST_PROXY=true`; de otro modo déjalo en `false`. Configura un límite de peticiones por IP en el proxy para proteger la inferencia pública. Tras configurar el dominio ejecuta `python manage.py check --deploy`. Las advertencias de HSTS para subdominios y precarga son intencionales, ya que esta demo no administra todos los subdominios del dominio de alojamiento. El contenedor no necesita SQL Server ni migraciones. No publiques el antiguo `venv/`, datos de entrenamiento ni archivos de conexión local.

Para construir y probar la imagen:

```sh
docker build -t loans-demo .
docker run --rm -p 8000:8000 -e DJANGO_DEBUG=true loans-demo
```

El comando anterior es solo para comprobarla en `localhost`. Para exponerla en Internet usa `DJANGO_DEBUG=false` y las variables de producción indicadas arriba.

En Render selecciona un **Web Service** con lenguaje **Docker** y este repositorio como origen. La imagen usa el puerto `PORT` que entrega Render. Define `DJANGO_ALLOWED_HOSTS` con el subdominio `*.onrender.com` exacto asignado al servicio, `DJANGO_CSRF_TRUSTED_ORIGINS` con su URL HTTPS y `DJANGO_TRUST_PROXY=true` después de confirmar que el proxy establece `X-Forwarded-Proto`. Mantén `WEB_CONCURRENCY=1` en una instancia pequeña.

El modelo `.pkl` es un artefacto local de confianza; no cargues modelos proporcionados por visitantes. El notebook original en `test/` documenta un experimento previo con 98 % de exactitud sobre su partición de prueba, pero esa cifra no ha sido revalidada como desempeño en población real. Antes de difundir el dataset o el reporte Power BI, confirma sus permisos de uso y procedencia.
