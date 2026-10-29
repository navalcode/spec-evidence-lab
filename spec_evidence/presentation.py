"""Optional human summaries; machine keys, statuses and specification hashes stay stable."""
from .contracts import ContractError

SUMMARIES = {
    'en': {
        'passed': 'Required test evidence is present and passing; review its provenance and adequacy.',
        'failed': 'Required evidence is incomplete or failing.',
        'ready_for_human_review': 'Proposal checks passed. Human review is required; no changes were executed.',
        'needs_revision': 'The proposal needs revision. No changes were executed.',
        'invalid_input': 'Input validation failed.',
        'digest': 'Specification digest computed; this does not execute tests.',
    },
    'es': {
        'passed': 'La evidencia requerida está presente y pasa; revisa su procedencia y suficiencia.',
        'failed': 'La evidencia requerida está incompleta o falla.',
        'ready_for_human_review': 'La propuesta supera las comprobaciones. Requiere revisión humana; no se ejecutaron cambios.',
        'needs_revision': 'La propuesta necesita revisión. No se ejecutaron cambios.',
        'invalid_input': 'La entrada no supera la validación.',
        'digest': 'Hash de especificación calculado; esta operación no ejecuta tests.',
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
        lines += ['', f'{"Criterios cubiertos" if es else "Covered criteria"}: {passed}/{len(criteria)}']
        for item in criteria:
            label = 'OK' if item['passed'] else ('REVISAR' if es else 'REVIEW')
            lines.append(f'  {label} {display_text(item["requirement"])} / {display_text(item["criterion"])}')
            for test in item['tests']:
                if test['status'] != 'passed':
                    lines.append(f'    {test["status"]}: {display_text(test["id"])}')
        if result['suite_failures']:
            lines.append('Fallos en la suite:' if es else 'Suite failures:')
            lines += [f'  {display_text(identifier)}' for identifier in result['suite_failures']]
        lines += ['', 'Revisa la procedencia de la evidencia y la suficiencia de los tests.' if es else
                  'Review evidence provenance and test adequacy.']
    if 'issues' in result:
        lines += ['', f'{"Incidencias" if es else "Issues"}: {len(result["issues"])}']
        lines += [f'  {item["code"]}: {display_text(item["message"])}' for item in result['issues']]
        lines.append('No se ejecutaron cambios.' if es else 'No changes were executed.')
    if 'error' in result:
        lines += ['', display_text(result['error'])]
    if 'spec_sha256' in result:
        lines += ['', f'Spec SHA-256: {result["spec_sha256"]}']
    return '\n'.join(lines)
