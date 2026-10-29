# Spec Evidence Lab

[English](README.md) · [![Checks](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml)

Demostración original que conecta una especificación, sus criterios de aceptación, resultados de tests y propuestas estructuradas de IA. La CLI utiliza la biblioteca estándar de Python. Un adaptador opcional expone las mismas comprobaciones mediante MCP por stdio.

## La pregunta de ingeniería

¿Qué permite distinguir un plan plausible de evidencias que cubren un contrato explícito?

La especificación declara identificadores estables, criterios de aceptación, tests esperados, rutas permitidas y exclusiones. El comprobador los relaciona con resultados JUnit. El revisor comprueba si una propuesta sigue vinculada a la especificación vigente y respeta su alcance.

Una propuesta válida queda preparada para revisión humana. La comprobación de resultados también exige revisar el significado de las pruebas y su procedencia. Ningún resultado del programa aprueba automáticamente un cambio.

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

El objeto añadido `presentation` contiene idioma y resumen. No cambian claves, estados, identidad de tests, códigos de salida ni hash de la especificación. Campos desconocidos, claves duplicadas, idiomas no soportados y entradas excesivas fallan. Diagnósticos y respuestas MCP conservan su contrato; esta función no traduce requisitos, evalúa prosa o aplica un prompt corporativo.

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

La validación cubre 40 tests de herramienta/configuración, cinco del ejemplo y cuatro comprobaciones del protocolo MCP. El alcance es demostrar un proceso verificable; no acreditar la autenticidad de reportes externos, demostrar cualquier requisito o medir productividad de un modelo.

La validación local utiliza Python 3.14. [GitHub Actions ha pasado en Python 3.11 y 3.14](https://github.com/navalcode/spec-evidence-lab/actions/runs/40882781413), con la comprobación MCP en 3.14. El distintivo enlaza los resultados actuales del workflow.

Referencia del adaptador opcional: [SDK oficial de MCP para Python](https://github.com/modelcontextprotocol/python-sdk).

## Licencia

Código y documentación originales: [MIT](LICENSE), copyright 2026 Manuel Naval. Las dependencias de terceros conservan sus propias licencias.
