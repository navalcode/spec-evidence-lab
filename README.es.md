# Spec Evidence Lab

[English](README.md) · [![Checks](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml)

CLI de Python para comparar los tests exigidos por una especificación con resultados JUnit y revisar propuestas estructuradas de cambios. Identifica tests ausentes, fallidos u omitidos y propuestas que no coinciden con el hash, los requisitos, los tests o las rutas permitidas.

La especificación declara IDs estables, tests esperados, rutas y exclusiones. Un resultado correcto indica coherencia con esas declaraciones. Quien revisa debe comprobar de dónde viene el informe y si los tests verifican el comportamiento previsto. Una propuesta válida sigue requiriendo revisión humana y no ejecuta cambios. La CLI usa la biblioteca estándar; un adaptador opcional expone las mismas comprobaciones por MCP sobre stdio.

## Ejecutar el ejemplo

Requiere Python 3.11 o superior. Desde esta carpeta:

```sh
python3 -m unittest discover -s tests -v
python3 tools/run_demo_tests.py --output artifacts/demo.xml
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal.json
```

El script ejecuta realmente los tests del catálogo ficticio y genera su reporte JUnit. Cubren caché, primer fallo sin datos, recuperación, reserva repetida e identificadores desconocidos. La propuesta de ejemplo es una entrada sintética con formato de planificación; no se atribuye a una llamada real a un modelo externo.

Para comprobar el rechazo de una propuesta obsoleta:

```sh
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal-stale.json
```

Devuelve código **1** y estado `needs_revision`. El subcomando `digest --spec ...` calcula el hash canónico de una especificación revisada.

## Comprobaciones

- Especificación: campos, identificadores únicos, aceptación, referencias de tests, rutas relativas y claves JSON duplicadas.
- JUnit: tests requeridos presentes una sola vez, resultados fallidos/omitidos diferenciados, recuentos contradictorios y errores sin testcase rechazados.
- Propuesta: hash vigente, requisitos y tests cubiertos, rutas dentro del alcance, cambios duplicados y preguntas pendientes.

Se admiten entradas de hasta 2 MiB. El JSON usa UTF-8, hasta 64 niveles de anidamiento, números finitos y enteros de hasta 128 dígitos. Se rechazan declaraciones DTD y entidades XML. Se soportan reportes `testsuite`/`testsuites` sin namespace y casos con `classname` y `name`. Los resultados se calculan a partir de los casos y se contrastan con los totales declarados. El programa no ejecuta órdenes del JSON, no inspecciona repositorios automáticamente y no modifica archivos.

Códigos de salida: **0** para resultado coherente, **1** para aceptación fallida o propuesta que necesita revisión y **2** para entrada inválida.

## Idioma y preferencias de proyecto

El reporte JSON predeterminado conserva su formato. Para añadir un resumen humano opcional, usa `--language en|es` o un archivo JSON acotado que contenga únicamente `language`. La opción explícita prevalece sobre el archivo:

```sh
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml --config examples/preferences.es.json
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal.json --config examples/preferences.es.json --language en
```

El objeto añadido `presentation` contiene idioma y resumen. No cambian claves, estados, identidad de tests, códigos de salida ni hash de la especificación. Campos desconocidos, claves duplicadas, idiomas no soportados y entradas excesivas fallan. Diagnósticos y respuestas MCP conservan su contrato; la preferencia de idioma solo afecta a la presentación.

## Revisión humana en el terminal

Usa `--format text` para leer un resultado breve con IDs de criterios/tests, códigos de incidencias y hash de la especificación. `--language en|es` selecciona el resumen; los códigos de incidencia se conservan y las explicaciones indican qué campo corregir. Los controles de terminal en identificadores se escapan. JSON sigue siendo el formato predeterminado y MCP no cambia.

```sh
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml --format text
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal-stale.json --format text --language es
python3 -m spec_evidence check --help
```

La salida de texto conserva los códigos: 0 para resultado coherente, 1 para evidencia fallida/revisión y 2 para entrada inválida. Un resumen correcto sigue requiriendo revisar la procedencia de la evidencia y suficiencia de los tests. [Decisiones de presentación](DESIGN.md).

## Servidor MCP opcional

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[mcp]'
.venv/bin/python tools/run_demo_tests.py --output artifacts/demo.xml
.venv/bin/python tools/check_mcp.py
```

La comprobación inicia un subproceso real, negocia MCP, descubre las herramientas, comprueba la salida estructurada, acepta evidencias válidas, rechaza una propuesta obsoleta y observa el error esperado ante un contrato inválido. Utiliza el cliente oficial del SDK; no certifica por sí sola la integración con cada IDE o asistente.

Entrada del servidor: `.venv/bin/python -m spec_evidence.mcp_server`. Expone `check_acceptance` y `review_ai_proposal`. Reciben contenidos, no rutas del equipo. Están anotadas como herramientas de solo lectura e idempotentes, no requieren credenciales o API de modelos y no abren un puerto de red.

## Recorrido del código

- [`contracts.py`](spec_evidence/contracts.py): contrato y hash canónico.
- [`evidence.py`](spec_evidence/evidence.py): trazabilidad de aceptación a pruebas.
- [`proposals.py`](spec_evidence/proposals.py): revisión de planificación estructurada.
- [`mcp_server.py`](spec_evidence/mcp_server.py): adaptador del protocolo.
- [`tests/`](tests/): casos positivos y negativos.
- [`examples/offline_catalog/`](examples/offline_catalog/): implementación, contrato y propuestas ficticias.

Comprobaciones actuales: **44 tests de validador/configuración/presentación, cinco del ejemplo y cuatro llamadas MCP reales**. [Verificación](docs/VERIFICATION.md), en inglés, recoge los comandos, la comparación de salidas de máquina, los fallos y los resultados de CI. El adaptador usa el [SDK oficial Python de MCP](https://github.com/modelcontextprotocol/python-sdk), fijado en 2.3.0.

## Licencia

Código y documentación originales: [MIT](LICENSE), copyright 2026 Manuel Naval. Las dependencias de terceros conservan sus propias licencias.
