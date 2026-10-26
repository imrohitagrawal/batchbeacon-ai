"""Controlled regressions for the observed subtitle inclusion; no model-efficacy claim.

The inert prompt proposal is never imported by application code. Responses below
are explicitly authored controls sent through installed ADK and mock HTTP.
"""

import copy
import json
from hashlib import sha256
from pathlib import Path

import pytest

from batchbeacon.model_runtime import PROMPT, ExtractionConfig
from tests.unit.test_extraction_proposal import known
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_reviewed_extraction import acquire, build_reviewed, view
from tests.unit.test_shared_admission import env as env  # noqa

CANDIDATE = json.loads(Path('tests/fixtures/name-field-prompt-candidate.json').read_text())
OBSERVED_NAME = 'Meadow Vale Brie\nInvented third identity'


def candidate_case(setup, env, indices=(2,)):
    return build_reviewed(setup, env, indices, extraction_overrides={
        'instruction': CANDIDATE['instruction'], 'prompt_version': CANDIDATE['prompt_version']})


def assert_no_publication(case, status, code, expected_state='REVIEW_REQUIRED'):
    assert status.state == expected_state and not status.current
    assert status.diagnostics == (code,)
    result = view(case)
    assert len(result.state.extractions) == 1
    assert result.state.extractions[0].envelope.values is None
    assert result.state.extractions[0].identity_receipt is None
    assert not result.state.observations and not result.state.results
    assert not result.hold_eligible
    assert len(case[4]) == 2  # one mock count, one mock generation; never a retry


@pytest.mark.parametrize('candidate', [False, True])
def test_observed_two_line_name_is_refused_without_trimming(setup, env, candidate):
    case = candidate_case(setup, env) if candidate else build_reviewed(setup, env)
    case[5][0]['label']['name'] = known(OBSERVED_NAME)
    case[5][0]['label']['name']['locations'][0]['box'] = [0.059, 0.252, 0.505, 0.404]
    original = copy.deepcopy(case[5][0])
    assert_no_publication(case, acquire(case), 'IDENTITY_EVIDENCE_DISAGREEMENT')
    assert case[5][0] == original


@pytest.mark.parametrize('index', [0, 1, 2])
def test_candidate_reaches_sealed_requests_without_changing_controlled_verdicts(setup, env, index):
    case = candidate_case(setup, env, (index,))
    status = acquire(case)
    result = view(case)
    assert status.state == 'COMPLETE' and status.current
    assert result.result.verdict == ('NOT_LISTED_IN_CHECKED_NOTICES' if index == 2
                                     else 'MATCHED_HOLD_FOR_REVIEW')
    assert result.hold_eligible is (index != 2)
    assert len(case[4]) == 2
    count, generation = (json.loads(request.content) for request in case[4])
    expected = (CANDIDATE['instruction']
                + '\n\nYou are an agent. Your internal name is "batchbeacon_extract".')
    assert count['systemInstruction']['parts'] == [{'text': expected}]
    assert generation['systemInstruction'] == count['systemInstruction']
    assert generation['contents'] == count['contents']
    assert generation['generationConfig'] == count['generationConfig']
    assert result.state.extractions[0].envelope.prompt_version == CANDIDATE['prompt_version']
    assert result.state.extractions[0].envelope.configuration_hash == case[0].config.digest()
    assert case[0].shared.policy.model_configuration_hash == case[0].config.digest()
    # Candidate text is not a catalog/expected-answer channel.
    assert all(entry.name not in expected
               for entry in case[0].evidence.identities.catalog.identities)


def test_genuine_line_wrap_is_preserved_verbatim_and_resolves(setup, env):
    case = candidate_case(setup, env)
    case[5][0]['label']['name'] = known('Meadow Vale\nBrie')
    assert acquire(case).state == 'COMPLETE'
    result = view(case)
    observed = result.state.extractions[0].envelope.values.identity.name
    assert observed.raw == observed.value == 'Meadow Vale\nBrie'
    assert result.observation.identity.resolved_name == 'Meadow Vale Brie'
    assert result.result.verdict == 'NOT_LISTED_IN_CHECKED_NOTICES'
    assert not result.hold_eligible


def test_candidate_does_not_allow_value_to_repair_observed_raw(setup, env):
    case = candidate_case(setup, env)
    case[5][0]['label']['name'] = known(OBSERVED_NAME)
    case[5][0]['label']['name']['value'] = 'Meadow Vale Brie'
    assert_no_publication(case, acquire(case), 'PROPOSAL_INVALID', expected_state='FAILED')


def test_ambiguous_field_boundary_does_not_become_nonmatch(setup, env):
    case = candidate_case(setup, env)
    case[5][0]['label']['name'] = known(OBSERVED_NAME)
    case[5][0]['label']['name'].update(state='AMBIGUOUS', value=None)
    status = acquire(case)
    result = view(case)
    assert status.state == 'REVIEW_REQUIRED'
    assert result.state.extractions[0].envelope.values.identity.name.raw == OBSERVED_NAME
    assert result.observation.identity.resolved_name is None
    assert result.result.verdict != 'NOT_LISTED_IN_CHECKED_NOTICES'
    assert not result.hold_eligible


@pytest.mark.parametrize('source_index', [0, 1])
def test_candidate_does_not_accept_recalled_name_for_third_image(setup, env, source_index):
    case = candidate_case(setup, env)
    case[5][0]['label']['name'] = known(case[5][0]['source']['products'][source_index]['name'])
    assert_no_publication(case, acquire(case), 'IDENTITY_EVIDENCE_DISAGREEMENT')


def test_inert_candidate_has_explicit_binding_and_does_not_replace_default():
    instruction = CANDIDATE['instruction']
    assert CANDIDATE['status'] == 'OFFLINE_PROPOSAL_NOT_ACTIVATED'
    assert sha256(instruction.encode()).hexdigest() == CANDIDATE['candidate_instruction_sha256']
    assert ExtractionConfig.model_fields['instruction'].default == PROMPT
    assert PROMPT != instruction
    assert ExtractionConfig.model_fields['prompt_version'].default != CANDIDATE['prompt_version']
