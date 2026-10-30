"""Optional human summaries; machine keys, statuses and specification hashes stay stable."""
from .contracts import ContractError

SUMMARIES = {
    'en': {
        'passed': 'All required tests are marked passed in the supplied report. Review its provenance and what the tests verify.',
        'failed': 'Some required tests are missing or not passing. Check the IDs below.',
        'ready_for_human_review': 'The proposal matches the declared scope and test plan. Human review is still required; no changes were executed.',
        'needs_revision': 'Revise the items listed below, then run review again. No changes were executed.',
        'invalid_input': 'The input could not be read or validated. Check the diagnostic below.',
        'digest': 'Specification SHA-256 computed. This command does not execute tests.',
    },
    'es': {
        'passed': 'Todos los tests exigidos figuran como aprobados en el informe. Revisa su procedencia y qué verifican.',
        'failed': 'Faltan tests exigidos o alguno no está aprobado. Revisa los identificadores indicados.',
        'ready_for_human_review': 'La propuesta coincide con el alcance y los tests declarados. Aún requiere revisión humana; no se ejecutaron cambios.',
        'needs_revision': 'Corrige los puntos indicados y vuelve a ejecutar review. No se ejecutaron cambios.',
        'invalid_input': 'No se ha podido leer o validar la entrada. Consulta el diagnóstico indicado.',
        'digest': 'SHA-256 de la especificación calculado. Este comando no ejecuta tests.',
    },
}


def configured_language(value):
    if type(value) is not dict or set(value) != {'language'}:
        raise ContractError('Configuration must contain only language')
    language = value['language']
    if type(language) is not str or language not in SUMMARIES:
        raise ContractError('Configuration language must be en or es')
    return language


def with_presentation(result, language):
    if language is None:
        return result
    return {**result, 'presentation': {'language': language, 'summary': SUMMARIES[language][result.get('status', 'digest')]}}


def display_text(value):
    """Keep untrusted identifiers readable without terminal control sequences."""
    return ''.join(char if char.isprintable() else f'\\u{ord(char):04x}' for char in str(value))


def render_text(result, language='en'):
    es = language == 'es'
    status = result.get('status', 'digest')
    lines = ['Spec Evidence Lab']
    if 'project' in result:
        lines.append(display_text(result['project']))
    lines += [status, SUMMARIES[language][status]]
    if 'criteria' in result:
        criteria = result['criteria']
        passed = sum(item['passed'] for item in criteria)
        lines += ['', f'{"Criterios con tests aprobados" if es else "Criteria with passing tests"}: {passed}/{len(criteria)}']
        for item in criteria:
            label = 'OK' if item['passed'] else ('REVISAR' if es else 'REVIEW')
            lines.append(f'  {label} {display_text(item["requirement"])} / {display_text(item["criterion"])}')
            for test in item['tests']:
                if test['status'] != 'passed':
                    lines.append(f'    {test["status"]}: {display_text(test["id"])}')
        if result['suite_failures']:
            lines.append('Fallos en la suite:' if es else 'Suite failures:')
            lines += [f'  {display_text(identifier)}' for identifier in result['suite_failures']]
        if status != 'passed':
            lines += ['', 'Ejecuta los tests exigidos y genera un nuevo JUnit. Revisa la procedencia del informe.' if es else
                      'Run the required tests and generate a fresh JUnit report. Check its provenance.']
    if 'issues' in result:
        lines += ['', f'{"Incidencias" if es else "Issues"}: {len(result["issues"])}']
        lines += [f'  {item["code"]}: {display_text(issue_guidance(item, language))}' for item in result['issues']]
        lines.append('No se ejecutaron cambios.' if es else 'No changes were executed.')
    if 'error' in result:
        lines += ['', display_text(result['error'])]
    if 'spec_sha256' in result:
        lines += ['', f'Spec SHA-256: {result["spec_sha256"]}']
    return '\n'.join(lines)


ISSUE_GUIDANCE = {
    'stale_spec': (
        'Re-read the current specification, revise the proposal, then update spec_sha256 using digest.',
        'Relee la especificación vigente, ajusta la propuesta y actualiza spec_sha256 con digest.'),
    'requirement_coverage': (
        'Make requirements list exactly the IDs declared in the specification.',
        'Incluye en requirements exactamente los IDs declarados en la especificación.'),
    'test_coverage': (
        'Make planned_tests match the test IDs in the acceptance criteria.',
        'Ajusta planned_tests a los IDs de tests de los criterios de aceptación.'),
    'path_out_of_scope': (
        'Use relative paths allowed by scope.paths. Review any scope change in the specification first.',
        'Usa rutas relativas permitidas por scope.paths. Revisa primero en la especificación cualquier cambio de alcance.'),
    'duplicate_path': (
        'Combine the edits for each path into one change entry.',
        'Agrupa los cambios de cada ruta en una sola entrada de changes.'),
    'unknown_requirement': (
        'Check each change’s requirement IDs against the specification.',
        'Comprueba los IDs de requisitos de cada cambio con la especificación.'),
    'unplanned_requirement': (
        'Add a proposed change for each uncovered requirement.',
        'Añade un cambio propuesto para cada requisito que aún no lo tenga.'),
    'unresolved_questions': (
        'Resolve the items in open_questions before submitting the proposal again.',
        'Resuelve los puntos de open_questions antes de volver a revisar la propuesta.'),
}


def issue_guidance(issue, language):
    messages = ISSUE_GUIDANCE.get(issue['code'])
    return messages[language == 'es'] if messages else issue['message']
