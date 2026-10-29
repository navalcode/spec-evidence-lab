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
