"""Tests del orquestador headless (SPEC-006 US1): run_batch, resiliencia, persistencia."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src import runner
from src.adapters.file_run_repository import FileRunRepository
from src.domain.agent_trace import AgentTrace, TraceStep
from src.domain.classification_evaluator import ClassificationEvaluator
from src.domain.ports import AgentResponse
from src.domain.result import TestResult
from src.domain.test_case import TestCase


def _case(case_id: str = "TC-1", clasif: str = "Verde") -> TestCase:
    return TestCase(
        id=case_id,
        nombre_iniciativa="Iniciativa X",
        intent_negocio=True,
        intent_operativo=False,
        intent_capacidad_equipos=False,
        intent_tecnico_arquitectural=False,
        declaracion_intent="x",
        area_proponente="x",
        flujo_de_valor="x",
        metricas_de_exito="x",
        impacto_personas="x",
        datos_ninguno=True,
        datos_publicos=False,
        datos_operativos=False,
        datos_personales=False,
        datos_confidenciales=False,
        datos_otros=False,
        datos_otros_mensaje="N/A",
        supuesto_riesgo="x",
        restricciones="x",
        sponsor="x",
        mail_contacto="x@x",
        clasificacion_esperada=clasif,
    )


class _StubClient:
    """Cliente del agente configurable para test, sin red."""

    def __init__(
        self,
        *,
        final_text: str = "La clasificacion es Verde",
        no_thread: bool = False,
        raise_on_send_call: int | None = None,
        interrupt_on_send_call: int | None = None,
        trace_raises: bool = False,
        overall_status: str = "completed",
    ) -> None:
        self._final_text = final_text
        self._no_thread = no_thread
        self._raise_on = raise_on_send_call
        self._interrupt_on = interrupt_on_send_call
        self._trace_raises = trace_raises
        self._overall_status = overall_status
        self.send_calls = 0
        self.trace_calls = 0

    def send(self, form: dict[str, Any], conversation_id: str | None = None) -> AgentResponse:
        self.send_calls += 1
        if self._interrupt_on is not None and self.send_calls == self._interrupt_on:
            raise KeyboardInterrupt  # simula Ctrl+C con el caso en vuelo (FR-US3-001)
        if self._raise_on is not None and self.send_calls == self._raise_on:
            raise RuntimeError("fallo simulado de envío")
        thread = None if self._no_thread else f"thread-{self.send_calls}"
        return AgentResponse(content="A new flow has started", conversation_id=thread)

    def wait_for_completion(self, thread_id: str, timeout_seconds: int = 300) -> bool:
        return True

    def get_thread_messages(self, thread_id: str) -> list[dict[str, Any]]:
        return [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "A new flow has started"},
            {"role": "assistant", "content": self._final_text},
        ]

    def get_final_response(self, thread_id: str, fallback_content: str) -> AgentResponse:
        for msg in self.get_thread_messages(thread_id):
            text = str(msg.get("content", ""))
            if msg.get("role") == "assistant" and "a new flow has started" not in text.lower():
                return AgentResponse(content=text, conversation_id=thread_id)
        return AgentResponse(content=fallback_content, conversation_id=thread_id)

    def get_trace(self, thread_id: str) -> AgentTrace:
        self.trace_calls += 1
        if self._trace_raises:
            raise RuntimeError("fallo simulado de get_trace")
        return AgentTrace(
            thread_id=thread_id,
            flow_id=f"flow-{thread_id}",
            overall_status=self._overall_status,
            steps=(TraceStep(step_id="s1", agent_name="Validador", status="completed"),),
        )


def test_run_batch_evaluates_all_cases() -> None:
    cases = (_case("TC-1"), _case("TC-2"), _case("TC-3"))
    results = runner.run_batch(cases, _StubClient(), ClassificationEvaluator())
    assert len(results) == 3
    assert all(r.verdict == "pass" for r in results)


def test_run_batch_captures_trace_per_case() -> None:
    cases = (_case("TC-1"), _case("TC-2"))
    client = _StubClient()
    results = runner.run_batch(cases, client, ClassificationEvaluator(), capture_traces=True)
    assert client.trace_calls == 2  # una captura por caso
    assert all(r.trace is not None for r in results)
    assert results[0].flow_id == "flow-thread-1"
    assert results[1].flow_id == "flow-thread-2"


def test_trace_capture_is_single_call_per_case() -> None:
    cases = (_case("TC-1"),)
    client = _StubClient()
    runner.run_batch(cases, client, ClassificationEvaluator(), capture_traces=True)
    assert client.trace_calls == 1  # única, sin poll (FR-US2-007)


def test_non_terminal_trace_is_persisted_as_is() -> None:
    cases = (_case("TC-1"),)
    client = _StubClient(overall_status="interrupted")
    results = runner.run_batch(cases, client, ClassificationEvaluator(), capture_traces=True)
    assert results[0].trace is not None
    assert results[0].trace.overall_status == "interrupted"  # tal cual, sin refresco


def test_trace_failure_does_not_abort_case() -> None:
    cases = (_case("TC-1"),)
    client = _StubClient(trace_raises=True)
    results = runner.run_batch(cases, client, ClassificationEvaluator(), capture_traces=True)
    assert results[0].verdict == "pass"  # el veredicto se preserva
    assert results[0].trace is None  # captura fallida → traza nula (FR-US2-005)


def test_run_batch_invokes_progress_callback_once_per_case() -> None:
    cases = (_case("TC-1"), _case("TC-2"), _case("TC-3"))
    seen: list[tuple[int, int, str]] = []

    def on_result(index: int, total: int, result: TestResult) -> None:
        seen.append((index, total, result.case_id))

    runner.run_batch(cases, _StubClient(), ClassificationEvaluator(), on_result=on_result)
    assert seen == [(1, 3, "TC-1"), (2, 3, "TC-2"), (3, 3, "TC-3")]


def test_run_one_emits_phases_in_order() -> None:
    # PhaseCallback (ADR-005 / SPEC-003 §Integración): fases agnósticas que cada
    # composition root traduce a su canal (widget de estado vs. stdout).
    seen: list[tuple[str, str]] = []
    result = runner.run_one(
        _case("TC-1"),
        _StubClient(),
        ClassificationEvaluator(),
        on_phase=lambda fase, detalle: seen.append((fase, detalle)),
    )
    assert result.verdict == "pass"
    assert seen == [("enviando", "TC-1"), ("esperando_flow", "thread-1")]


def test_run_one_without_thread_id_stops_phases_at_enviando() -> None:
    seen: list[str] = []
    runner.run_one(
        _case("TC-1"),
        _StubClient(no_thread=True),
        ClassificationEvaluator(),
        on_phase=lambda fase, _detalle: seen.append(fase),
    )
    assert seen == ["enviando"]


def test_is_execution_failure_distinguishes_from_genuine_indeterminate() -> None:
    from src.application.run_suite import execution_failure, is_execution_failure

    failure = execution_failure(_case("TC-1"), "timeout simulado")
    assert is_execution_failure(failure) is True

    # Indeterminado genuino: el agente respondió pero sin clasificación extraíble.
    genuine = runner.run_one(
        _case("TC-1"), _StubClient(final_text="sin color aqui"), ClassificationEvaluator()
    )
    assert genuine.verdict == "indeterminado"
    assert is_execution_failure(genuine) is False

    passed = runner.run_one(_case("TC-1"), _StubClient(), ClassificationEvaluator())
    assert is_execution_failure(passed) is False


def test_total_metrics_title_has_single_canonical_wording() -> None:
    # SPEC-008 FR-010: redacción única del título, compartida por runner y dashboard.
    from src.application.generate_metrics_report import total_metrics_title
    from src.domain.result import SuiteResult

    run = SuiteResult.create((TestResult("c1", "Verde", "...", "Verde", True),), agent_id="agent-x")
    assert (
        total_metrics_title([run, run]) == "Matriz de confusión — total (2 corrida(s), 2 caso(s))"
    )


def test_send_without_thread_id_yields_indeterminate_without_aborting() -> None:
    cases = (_case("TC-1"), _case("TC-2"))
    results = runner.run_batch(cases, _StubClient(no_thread=True), ClassificationEvaluator())
    assert len(results) == 2
    assert all(r.verdict == "indeterminado" for r in results)
    assert "Error de ejecución" in results[0].notes


def test_unexpected_exception_does_not_abort_suite() -> None:
    cases = (_case("TC-1"), _case("TC-2"), _case("TC-3"))
    client = _StubClient(raise_on_send_call=2)
    results = runner.run_batch(cases, client, ClassificationEvaluator())
    assert len(results) == 3
    assert results[0].verdict == "pass"
    assert results[1].verdict == "indeterminado"  # el que lanzó excepción
    assert results[2].verdict == "pass"


def test_run_batch_stops_on_interrupt_discarding_in_flight_case() -> None:
    # El 2º caso se interrumpe (Ctrl+C): TC-1 completó, TC-2 queda en vuelo y se
    # descarta, TC-3 no se lanza (SPEC-006 FR-US3-001).
    cases = (_case("TC-1"), _case("TC-2"), _case("TC-3"))
    results = runner.run_batch(
        cases, _StubClient(interrupt_on_send_call=2), ClassificationEvaluator()
    )
    assert len(results) == 1
    assert results[0].case_id == "TC-1"
    assert results[0].verdict == "pass"


def test_build_suite_persists_partial_run_after_interrupt(tmp_path: Path) -> None:
    # La corrida parcial se arma y persiste por la misma ruta que una completa, y
    # sobrevive el round-trip como una corrida de K casos (FR-US3-002/004).
    cases = (_case("TC-1"), _case("TC-2"), _case("TC-3"))
    suite = runner.build_suite(
        cases, _StubClient(interrupt_on_send_call=3), ClassificationEvaluator(), agent_id="agent-x"
    )
    assert suite.total == 2
    saved = FileRunRepository(tmp_path).save(suite)
    reloaded = FileRunRepository(tmp_path).load_all()
    assert len(reloaded) == 1
    assert reloaded[0].total == 2
    assert Path(saved).exists()


def test_build_suite_persists_single_run_with_n_results(tmp_path: Path) -> None:
    cases = (_case("TC-1"), _case("TC-2"))
    suite = runner.build_suite(cases, _StubClient(), ClassificationEvaluator(), agent_id="agent-x")
    saved = FileRunRepository(tmp_path).save(suite)
    assert Path(saved).exists()
    assert suite.total == 2
    assert suite.agent_id == "agent-x"


def test_main_returns_1_when_file_missing(tmp_path: Path, capsys: Any) -> None:
    missing = tmp_path / "no-existe.csv"
    code = runner.main(["--in", str(missing), "--out", str(tmp_path)])
    assert code == 1
    assert "No se pudo leer el archivo" in capsys.readouterr().err


def test_main_returns_1_when_file_empty(tmp_path: Path, capsys: Any) -> None:
    empty = tmp_path / "vacio.csv"
    empty.write_text("   ", encoding="utf-8")
    code = runner.main(["--in", str(empty), "--out", str(tmp_path)])
    assert code == 1
    assert "inválido" in capsys.readouterr().err


def test_format_metrics_report_includes_matrix_and_summary() -> None:
    from src.domain.metrics import compute_suite_metrics
    from src.domain.result import SuiteResult

    def _res(case_id: str, expected: str, extracted: str | None) -> TestResult:
        passed = None if extracted is None else extracted == expected
        return TestResult(
            case_id=case_id,
            expected=expected,
            actual_response="...",
            extracted_classification=extracted,
            passed=passed,
        )

    run = SuiteResult.create(
        (_res("c1", "Verde", "Verde"), _res("c2", "Rojo", None)), agent_id="agent-x"
    )
    from src.domain.metrics import format_metrics_report

    report = format_metrics_report(compute_suite_metrics(run), "Titulo X")
    assert report.startswith("# Titulo X")
    assert "esperado;Verde;Amarillo;Rojo;Negro;Rechazado;Sin clasificación" in report
    assert "# Resumen de estadística" in report
    assert "# Accuracy por clase" in report
    assert "total_casos;2" in report


def test_format_metrics_markdown_renders_aligned_tables() -> None:
    from src.domain.metrics import compute_suite_metrics
    from src.domain.result import SuiteResult

    run = SuiteResult.create(
        (
            TestResult("c1", "Verde", "...", "Verde", True),
            TestResult("c2", "Rojo", "...", None, None),
        ),
        agent_id="agent-x",
    )
    md = runner.format_metrics_markdown(compute_suite_metrics(run), "Titulo X")
    assert md.startswith("## Titulo X")
    # encabezado y separador de tabla Markdown
    assert "| esperado \\ detectado" in md
    assert "| :---" in md and "---:" in md  # fila separadora con alineación
    assert "### Resumen de estadística" in md
    assert "### Accuracy por clase" in md


def test_main_estadistica_prints_markdown_and_writes_csv(tmp_path: Path, capsys: Any) -> None:
    suite = runner.build_suite(
        (_case("TC-1", "Verde"), _case("TC-2", "Verde")),
        _StubClient(),
        ClassificationEvaluator(),
        agent_id="agent-x",
    )
    FileRunRepository(tmp_path).save(suite)

    code = runner.main(["--estadistica", "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    # pantalla en Markdown (tabla con barras)
    assert "## Matriz de confusión — total" in out
    assert "|" in out
    # archivo en CSV (delimitado por ';')
    written = tmp_path / "stats" / "estadistica-matriz.csv"
    assert written.exists()
    content = written.read_text(encoding="utf-8")
    assert "# Resumen de estadística" in content
    assert ";" in content and "|" not in content


def test_main_estadistica_returns_1_without_runs(tmp_path: Path, capsys: Any) -> None:
    code = runner.main(["--estadistica", "--out", str(tmp_path)])
    assert code == 1
    assert "No hay corridas" in capsys.readouterr().err


def test_main_requires_in_without_estadistica(tmp_path: Path, capsys: Any) -> None:
    code = runner.main(["--out", str(tmp_path)])
    assert code == 2
    assert "Falta --in" in capsys.readouterr().err


# --- main: camino completo con config y cliente stubeados (SPEC-006 US1) ---

_HEADER = (
    "id;nombre_iniciativa;intent_negocio;intent_operativo;intent_capacidad_equipos;"
    "intent_tecnico_arquitectural;declaracion_intent;area_proponente;flujo_de_valor;"
    "metricas_de_exito;impacto_personas;datos_ninguno;datos_publicos;datos_operativos;"
    "datos_personales;datos_confidenciales;datos_otros;supuesto_riesgo;restricciones;"
    "sponsor;mail_contacto;clasificacion_esperada;marcadores"
)


def _csv_row(case_id: str = "TC-1", *, nombre: str = "Iniciativa X") -> str:
    return (
        f"{case_id};{nombre};true;false;false;false;decl;area;flujo;metricas;"
        "impacto;true;false;false;false;false;false;riesgo;restric;sponsor;"
        "a@b.com;Verde;"
    )


class _StubConfig:
    agent_id = "agent-x"


def _patch_composition(monkeypatch: Any, client: _StubClient) -> None:
    """Sustituye config, credenciales y cliente en el composition root: sin entorno ni red."""
    monkeypatch.setattr(runner.PlatformConfig, "from_env", staticmethod(lambda: _StubConfig()))
    monkeypatch.setattr(runner, "TokenProvider", lambda config: None)
    monkeypatch.setattr(
        runner,
        "RemoteAgentClient",
        lambda config, credentials, timeout_seconds: client,
    )


def _write_batch(tmp_path: Path, *rows: str) -> Path:
    batch = tmp_path / "casos.csv"
    batch.write_text("\n".join([_HEADER, *rows]), encoding="utf-8")
    return batch


def test_main_happy_path_persists_and_reports(
    tmp_path: Path, capsys: Any, monkeypatch: Any
) -> None:
    _patch_composition(monkeypatch, _StubClient())
    batch = _write_batch(tmp_path, _csv_row("TC-1"), _csv_row("TC-2"))

    code = runner.main(["--in", str(batch), "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Ejecutando 2 caso(s)" in captured.out
    assert "[1/2] TC-1 -> pass" in captured.out
    assert "2/2 pass" in captured.out
    assert "Detalle guardado en:" in captured.out
    reloaded = FileRunRepository(tmp_path).load_all()
    assert len(reloaded) == 1
    assert reloaded[0].total == 2


def test_main_reports_invalid_rows_and_still_runs_valid_ones(
    tmp_path: Path, capsys: Any, monkeypatch: Any
) -> None:
    _patch_composition(monkeypatch, _StubClient())
    batch = _write_batch(tmp_path, _csv_row("TC-1"), _csv_row("TC-2", nombre=""))

    code = runner.main(["--in", str(batch), "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "[fila 3] inválida" in captured.err
    assert "Filas inválidas omitidas: 1" in captured.err
    assert "Ejecutando 1 caso(s)" in captured.out


def test_main_returns_1_when_no_valid_cases(tmp_path: Path, capsys: Any) -> None:
    batch = _write_batch(tmp_path, _csv_row("TC-1", nombre=""))
    code = runner.main(["--in", str(batch), "--out", str(tmp_path)])
    assert code == 1
    assert "No hay casos válidos" in capsys.readouterr().err


def test_main_interrupt_persists_partial_run(tmp_path: Path, capsys: Any, monkeypatch: Any) -> None:
    # Ctrl+C en el 2º caso: la corrida parcial de 1 caso se persiste (FR-US3-002).
    _patch_composition(monkeypatch, _StubClient(interrupt_on_send_call=2))
    batch = _write_batch(tmp_path, _csv_row("TC-1"), _csv_row("TC-2"), _csv_row("TC-3"))

    code = runner.main(["--in", str(batch), "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Frenado manual: 1 de 3 caso(s) completado(s)" in captured.out
    reloaded = FileRunRepository(tmp_path).load_all()
    assert len(reloaded) == 1
    assert reloaded[0].total == 1


def test_main_interrupt_on_first_case_persists_nothing(
    tmp_path: Path, capsys: Any, monkeypatch: Any
) -> None:
    _patch_composition(monkeypatch, _StubClient(interrupt_on_send_call=1))
    batch = _write_batch(tmp_path, _csv_row("TC-1"), _csv_row("TC-2"))

    code = runner.main(["--in", str(batch), "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "No se completó ningún caso" in captured.err
    assert FileRunRepository(tmp_path).load_all() == []


# --- main --estadistica: ramas de error de persistencia (SPEC-008) ---


def test_main_estadistica_returns_1_when_runs_unreadable(
    tmp_path: Path, capsys: Any, monkeypatch: Any
) -> None:
    from src.adapters.file_run_repository import RunPersistenceError

    def _raise(self: FileRunRepository) -> None:
        raise RunPersistenceError("disco simulado ilegible")

    monkeypatch.setattr(FileRunRepository, "load_all", _raise)
    code = runner.main(["--estadistica", "--out", str(tmp_path)])
    assert code == 1
    assert "No se pudieron leer las corridas" in capsys.readouterr().err


def test_main_estadistica_reports_but_survives_csv_save_failure(
    tmp_path: Path, capsys: Any, monkeypatch: Any
) -> None:
    # El reporte a pantalla no se pierde aunque el CSV no se pueda escribir.
    from src.adapters.file_run_repository import RunPersistenceError

    suite = runner.build_suite(
        (_case("TC-1"),), _StubClient(), ClassificationEvaluator(), agent_id="agent-x"
    )
    FileRunRepository(tmp_path).save(suite)

    def _raise(repo: FileRunRepository, title: str) -> str:
        raise RunPersistenceError("escritura simulada fallida")

    monkeypatch.setattr(runner, "generate_metrics_report", _raise)
    code = runner.main(["--estadistica", "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "## Matriz de confusión — total" in captured.out
    assert "NO se pudo guardar el CSV" in captured.err
