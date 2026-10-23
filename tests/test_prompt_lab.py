from cfl.labs.catalog import LABS, STATUSES
from cfl.labs.prompt_lab import PROMPT_LABS, auto_evaluate, render_prompt


def test_prompts_render_with_document():
    for lab in PROMPT_LABS.values():
        for prompt in lab.prompts:
            text = render_prompt(lab, prompt)
            assert "{{DOCUMENTO}}" not in text
            assert "sintétic" in text.lower()  # el insumo se declara sintético


def test_improved_prompt_is_more_specific_than_initial():
    lab = PROMPT_LABS["01"]
    initial, improved = (render_prompt(lab, p) for p in lab.prompts)
    assert len(improved) > len(initial)
    for marker in ("<notas_reunion>", "Preguntas abiertas", "No inventes", "Dado/Cuando/Entonces"):
        assert marker in improved and marker not in initial


def test_auto_evaluate_on_a_handwritten_fixture():
    # Fixture escrito a mano para probar el evaluador; NO es una salida de Claude.
    fixture = "\n".join([
        "# Resumen y alcance", "## Requisitos funcionales", "RF-01 x", "RF-02 y", "## Requisitos no funcionales", "RNF-01 z",
        "## Flujo de integración", "idempotencia; webhooks duplicados", "## Mapeo de estados", "## Manejo de errores",
        "## Supuestos", "SUPUESTO: algo", "## Preguntas abiertas", "¿cancelar? ¿decimales? ¿IPs?",
        "## Criterios de aceptación", "Dado un pago, cuando hay timeout, entonces no se duplica.",
    ])
    result = auto_evaluate(fixture)
    assert result["C1_secciones_presentes"] == "9/9" and result["C1_en_orden"] is True
    assert result["C2_rf_numerados"] == 2 and result["C2_rnf_numerados"] == 1
    assert result["C5_idempotencia"] and result["C5_webhooks_duplicados_o_desorden"]
    assert result["C7_dado_cuando_entonces"] == 1


def test_catalog_uses_allowed_statuses():
    assert {lab.status for lab in LABS} <= set(STATUSES)
