"""Dashboard del modo simple: un caso por pantalla.

Tajada vertical completa: form -> validacion -> envio al agente ->
evaluacion -> veredicto. Ver specs/SPEC-001 y SPEC-003.

El framework UI concreto se importa solo aqui dentro para mantener el
resto del sistema agnostico (ver specs/SPEC-000-naming.md).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, cast

import streamlit as ui  # alias agnostico

from src.adapters.file_run_repository import FileRunRepository, RunPersistenceError
from src.adapters.platform_config import MissingConfigError, PlatformConfig
from src.adapters.remote_agent_client import RemoteAgentClient
from src.adapters.token_provider import TokenError, TokenProvider
from src.application.run_suite import execution_failure, run_one
from src.build import message_builder
from src.build.batch_loader import BatchLoadError, load_batch
from src.build.case_loader import CaseLoadError
from src.build.case_loader import load as load_case
from src.dashboard.trace_panel import render_trace
from src.domain.agent_trace import AgentTrace
from src.domain.classification_evaluator import ClassificationEvaluator
from src.domain.message_text import extract_message_text
from src.domain.metrics import (
    SIN_CLASIFICACION,
    SuiteMetrics,
    aggregate_suite_metrics,
    compute_suite_metrics,
)
from src.domain.result import SuiteResult, TestResult, aggregate_runs
from src.domain.test_case import PALETA_CLASIFICACION, TestCase


def _render_identificacion(g: int) -> tuple[str, str]:
    ui.subheader("Identificación del caso")
    case_id = ui.text_input(
        "ID del caso (opcional — se genera si se deja vacío)",
        key=f"case_id_{g}",
    )
    nombre = ui.text_input("Nombre de la iniciativa", key=f"nombre_{g}")
    return case_id, nombre


def _render_intent(g: int) -> dict[str, bool]:
    ui.subheader("Tipo de intent (al menos uno)")
    col1, col2 = ui.columns(2)
    with col1:
        negocio = ui.checkbox("Negocio", key=f"negocio_{g}")
        operativo = ui.checkbox("Operativo", key=f"operativo_{g}")
    with col2:
        equipos = ui.checkbox("Capacidad de equipos", key=f"equipos_{g}")
        tecnico = ui.checkbox("Tecnico / arquitectural", key=f"tecnico_{g}")
    return {
        "negocio": negocio,
        "operativo": operativo,
        "capacidad_equipos": equipos,
        "tecnico_arquitectural": tecnico,
    }


def _render_declaracion(g: int) -> dict[str, str]:
    ui.subheader("Declaración y contexto")
    return {
        "declaracion_intent": ui.text_area("Declaracion del intent", key=f"decl_{g}"),
        "area_proponente": ui.text_input("Area proponente", key=f"area_{g}"),
        "flujo_de_valor": ui.text_input("Flujo de valor", key=f"flujo_{g}"),
        "metricas_de_exito": ui.text_area("Metricas de exito", key=f"metricas_{g}"),
        "impacto_personas": ui.text_area("Impacto en personas", key=f"impacto_{g}"),
    }


def _render_datos(g: int) -> dict[str, bool | str]:
    ui.subheader("Datos requeridos (al menos uno)")
    col1, col2 = ui.columns(2)
    with col1:
        ninguno = ui.checkbox("Ninguno", key=f"ninguno_{g}")
        publicos = ui.checkbox("Publicos", key=f"publicos_{g}")
        operativos = ui.checkbox("Operativos", key=f"operativos_{g}")
    with col2:
        personales = ui.checkbox("Personales", key=f"personales_{g}")
        confidenciales = ui.checkbox("Confidenciales", key=f"confidenciales_{g}")
        otros = ui.checkbox("Otros", key=f"otros_{g}")
    otros_mensaje = ui.text_input(
        "Descripcion de otros datos (requerido si 'Otros' esta marcado)",
        disabled=not otros,
        placeholder="Describe el tipo de dato...",
        key=f"otros_msg_{g}",
    )
    return {
        "ninguno": ninguno,
        "publicos": publicos,
        "operativos": operativos,
        "personales": personales,
        "confidenciales": confidenciales,
        "otros": otros,
        "otros_mensaje": otros_mensaje,
    }


def _render_contexto_extra(g: int) -> dict[str, str]:
    ui.subheader("Riesgo y contacto")
    return {
        "supuesto_riesgo": ui.text_area("Supuesto / riesgo", key=f"riesgo_{g}"),
        "restricciones": ui.text_area("Restricciones", key=f"restricciones_{g}"),
        "sponsor": ui.text_input("Sponsor", key=f"sponsor_{g}"),
        "mail_contacto": ui.text_input("Mail de contacto", key=f"mail_{g}"),
    }


def _render_esperado(g: int) -> tuple[str, list[str]]:
    ui.subheader("Resultado esperado (clasificación de riesgo)")
    clasificacion = ui.selectbox(
        "Clasificacion esperada",
        options=list(PALETA_CLASIFICACION),
        index=0,
        key=f"clasif_{g}",
    )
    marcadores_raw = ui.text_input(
        "Marcadores (separados por coma)",
        placeholder="riesgo-alto, datos-personales",
        key=f"marcadores_{g}",
    )
    marcadores = [m.strip() for m in marcadores_raw.split(",") if m.strip()]
    return clasificacion, marcadores


def _build_case(
    case_id: str,
    nombre: str,
    intent: dict[str, bool],
    declaracion: dict[str, str],
    datos: dict[str, bool | str],
    contexto: dict[str, str],
    clasificacion: str,
    marcadores: list[str],
) -> TestCase:
    effective_id = case_id.strip() or f"TC-{uuid.uuid4().hex[:8].upper()}"
    return TestCase(
        id=effective_id,
        nombre_iniciativa=nombre,
        intent_negocio=bool(intent["negocio"]),
        intent_operativo=bool(intent["operativo"]),
        intent_capacidad_equipos=bool(intent["capacidad_equipos"]),
        intent_tecnico_arquitectural=bool(intent["tecnico_arquitectural"]),
        declaracion_intent=declaracion["declaracion_intent"],
        area_proponente=declaracion["area_proponente"],
        flujo_de_valor=declaracion["flujo_de_valor"],
        metricas_de_exito=declaracion["metricas_de_exito"],
        impacto_personas=declaracion["impacto_personas"],
        datos_ninguno=bool(datos["ninguno"]),
        datos_publicos=bool(datos["publicos"]),
        datos_operativos=bool(datos["operativos"]),
        datos_personales=bool(datos["personales"]),
        datos_confidenciales=bool(datos["confidenciales"]),
        datos_otros=bool(datos["otros"]),
        datos_otros_mensaje=str(datos["otros_mensaje"]),
        supuesto_riesgo=contexto["supuesto_riesgo"],
        restricciones=contexto["restricciones"],
        sponsor=contexto["sponsor"],
        mail_contacto=contexto["mail_contacto"],
        clasificacion_esperada=clasificacion,
        marcadores=tuple(marcadores),
    )


def _build_runtime() -> tuple[PlatformConfig, RemoteAgentClient, ClassificationEvaluator] | None:
    """Construye config + cliente + evaluador, o muestra el error y devuelve None."""
    try:
        config = PlatformConfig.from_env()
    except MissingConfigError as err:
        ui.error(f"Configuracion incompleta: {err}")
        return None

    credentials = TokenProvider(config)
    try:
        credentials.get()
    except TokenError as err:
        ui.error(f"Auth fallo: {err}")
        return None

    client = RemoteAgentClient(config, credentials, timeout_seconds=120)
    return config, client, ClassificationEvaluator()


def _send_and_evaluate(case: TestCase, *, fetch_trace: bool = False) -> None:
    runtime = _build_runtime()
    if runtime is None:
        return
    config, client, evaluator = runtime

    form = message_builder.build(case)
    with ui.spinner("Enviando al agente..."):
        trigger_response = client.send(form)

    thread_id = trigger_response.conversation_id
    if not thread_id:
        ui.error(f"El agente no devolvio thread_id. Respuesta: {trigger_response.content}")
        return

    ui.info(f"Flow iniciado. thread_id: `{thread_id}`. Esperando respuesta final...")
    with ui.spinner("Esperando que el agente complete el flow..."):
        completed = client.wait_for_completion(thread_id, timeout_seconds=300)

    if not completed:
        ui.error("El agente no respondio en el tiempo esperado.")
        return

    messages = client.get_thread_messages(thread_id)  # crudo, para el panel de display
    agent_response = client.get_final_response(thread_id, trigger_response.content)
    trace = client.get_trace(thread_id) if fetch_trace else None

    result = evaluator.evaluate(case, agent_response)

    run = SuiteResult.create((result,), agent_id=config.agent_id)
    saved_path: str | None = None
    persist_error: str | None = None
    try:
        saved_path = FileRunRepository().save(run)
    except RunPersistenceError as err:
        persist_error = str(err)

    ui.session_state["eval_result"] = {
        "result": result,
        "messages": messages,
        "trace": trace,
        "thread_id": thread_id,
        "saved_path": saved_path,
        "persist_error": persist_error,
    }


def _refresh_trace(thread_id: str) -> None:
    """Vuelve a pedir la traza: el flow cierra tareas (actualizar/send_mail) después
    de depositar la clasificación, así que un primer fetch puede verlo `interrupted`."""
    runtime = _build_runtime()
    if runtime is None:
        return
    _config, client, _evaluator = runtime
    eval_data = ui.session_state.get("eval_result")
    if isinstance(eval_data, dict):
        eval_data["trace"] = client.get_trace(thread_id)
        ui.session_state["eval_result"] = eval_data
    ui.rerun()


def _render_eval_result(data: dict[str, object]) -> None:
    result = cast(TestResult, data["result"])
    messages = cast(list[dict[str, object]], data["messages"])

    if result.passed is True:
        ui.success(f"PASS — esperado y obtenido coinciden ({result.expected}).")
    elif result.passed is False:
        ui.error(
            f"FAIL — esperado '{result.expected}', obtenido '{result.extracted_classification}'."
        )
    else:
        ui.warning(f"INDETERMINADO — {result.notes}")

    col1, col2 = ui.columns(2)
    with col1:
        ui.metric("Esperado", result.expected)
    with col2:
        ui.metric("Detectado", result.extracted_classification or "—")

    ui.markdown("**Respuesta completa del agente:**")
    ui.markdown(result.actual_response or "_(vacia)_")

    if result.conversation_id:
        ui.caption(f"conversation_id: `{result.conversation_id}`")

    persist_error = cast("str | None", data.get("persist_error"))
    saved_path = cast("str | None", data.get("saved_path"))
    if persist_error:
        ui.error(f"El resultado se mostro pero NO se pudo persistir: {persist_error}")
    elif saved_path:
        ui.caption(f"Resultado guardado en: `{saved_path}`")

    with ui.expander("Todos los mensajes del thread"):
        for msg in messages:
            role = msg.get("role", "?")
            text = extract_message_text(msg.get("content", ""))
            ui.markdown(f"**{role}:** {text}")
            ui.divider()

    with ui.expander("Detalle del TestResult"):
        ui.json(result.to_dict())

    trace = cast("AgentTrace | None", data.get("trace"))
    if trace is not None:
        with ui.expander("Traza de ejecución", expanded=False):
            render_trace(trace)
            thread_id = cast("str | None", data.get("thread_id"))
            if thread_id is not None:
                if trace.overall_status not in ("completed", "failed"):
                    ui.caption(
                        "El flow seguía cerrando tareas internas cuando se capturó la traza "
                        f"(estado: {trace.overall_status}). El veredicto no cambia; "
                        "actualizá para ver el cierre completo."
                    )
                if ui.button("Actualizar traza", key="refresh_trace"):
                    _refresh_trace(thread_id)


_TODAS_LAS_CORRIDAS = "— Todas las corridas (matriz general) —"


def _render_latest_run() -> None:
    """Revisa una corrida persistida sin re-ejecutar: selector de run + métricas
    (SPEC-005 FR-007 / SPEC-008). El selector incluye una opción agregada que
    cubre todos los casos de todas las corridas. Por defecto, la más reciente."""
    try:
        runs = FileRunRepository().load_all()
    except RunPersistenceError as err:
        ui.warning(f"No se pudo leer las corridas guardadas: {err}")
        return
    if not runs:
        ui.caption("Todavia no hay corridas guardadas.")
        return

    by_id = {run.run_id: run for run in runs}
    run_ids = sorted(by_id, reverse=True)  # run_id es timestamp: más reciente primero
    # Opción agregada: matriz sobre todos los casos de todas las corridas (FR-007).
    opciones = [_TODAS_LAS_CORRIDAS, *run_ids]
    chosen = ui.selectbox(
        "Corrida a revisar", opciones, index=1, key="saved_run_pick"
    )  # index=1 = corrida más reciente por defecto (FR-006)

    if chosen == _TODAS_LAS_CORRIDAS:
        ui.caption(f"Agregado sobre {len(runs)} corrida(s) guardada(s).")
        _render_metrics_block(aggregate_suite_metrics(runs))
        return

    run = by_id[chosen]
    ui.caption(f"run_id: `{run.run_id}` — {run.timestamp} — agent_id: `{run.agent_id}`")
    s = run.summary
    cols = ui.columns(4)
    cols[0].metric("Total", s["total"])
    cols[1].metric("Pass", s["pass"])
    cols[2].metric("Fail", s["fail"])
    cols[3].metric("Indeterminado", s["indeterminado"])

    _render_suite_metrics(run)

    ui.markdown("**Detalle por caso:**")
    ui.table(
        [
            {
                "case_id": r.case_id,
                "esperado": r.expected,
                "detectado": r.extracted_classification or "—",
                "veredicto": r.verdict,
            }
            for r in run.results
        ]
    )
    for r in run.results:
        with ui.expander(f"{r.case_id} → {r.verdict}"):
            cols = ui.columns(2)
            cols[0].metric("Esperado", r.expected)
            cols[1].metric("Detectado", r.extracted_classification or "—")
            if r.notes:
                ui.caption(r.notes)
            ui.markdown(r.actual_response or "_(respuesta vacía)_")
            if r.conversation_id:
                ui.caption(f"conversation_id: `{r.conversation_id}`")
            _render_case_trace(r, key_prefix="saved")

    ui.json(run.to_dict())


_BATCH_RUN_KEYS = (
    "batch_phase",
    "batch_pending",
    "batch_done",
    "batch_total",
    "batch_agent_id",
    "batch_traces",
    "batch_client",
    "batch_evaluator",
)


def _clear_batch_run_state(state: Any) -> None:
    """Descarta el resultado batch en pantalla y todo estado de una corrida en curso.

    Se usa al subir un archivo distinto al anterior (SPEC-006 FR-US1, MUST): el display
    de la corrida previa no debe mezclarse con el nuevo archivo, y una corrida a medio
    ejecutar del archivo viejo no debe seguir corriendo bajo el nuevo. No toca
    `batch_file_key` (la fija el caller con la clave del archivo nuevo).

    `state` es una bolsa tipo dict (el estado de sesión de la interfaz en producción, un
    `dict` en los tests); se tipa laxo para no acoplar el helper al framework de UI."""
    state.pop("batch_result", None)
    for key in _BATCH_RUN_KEYS:
        state.pop(key, None)


def _render_batch(g: int) -> None:
    """Carga un archivo batch, ejecuta la suite y muestra resultados conjuntos (US1)."""
    uploaded = ui.file_uploader(
        "Sube un archivo de casos (CSV; separador ; o ,)",
        type=["csv", "txt"],
        key=f"batch_upload_{g}",
    )
    if uploaded is None:
        return

    raw = uploaded.getvalue()

    # Si el archivo cambió respecto al anterior, descartar el resultado batch previo y
    # cualquier corrida en curso, para no mezclar corridas de archivos distintos
    # (SPEC-006 FR-US1, MUST "al subir un archivo distinto al anterior"). La clave es el
    # hash del contenido: dos archivos con igual nombre y tamaño pero distinto contenido
    # cuentan como distintos.
    file_key = hashlib.sha256(raw).hexdigest()
    if ui.session_state.get("batch_file_key") != file_key:
        ui.session_state["batch_file_key"] = file_key
        _clear_batch_run_state(ui.session_state)

    try:
        loaded = load_batch(raw)
    except BatchLoadError as err:
        ui.error(f"No se pudo leer el archivo: {err}")
        return

    ui.caption(f"{len(loaded.cases)} caso(s) válido(s), {len(loaded.errors)} fila(s) inválida(s).")
    if loaded.errors:
        with ui.expander("Filas inválidas (no se ejecutan)"):
            for row_err in loaded.errors:
                ui.markdown(f"- fila {row_err.line}: {row_err.message}")
    if not loaded.cases:
        return

    fetch_traces = ui.checkbox(
        "Capturar trazas de ejecución (una llamada extra por caso)",
        value=False,
        key=f"batch_traces_{g}",
    )

    # La corrida es interrumpible: se ejecuta un caso por tick cediendo el control
    # a la interfaz entre casos, para que el botón "Frenar" sea atendido a mitad de
    # la corrida (SPEC-006 FR-US3-003). Frenar cierra la corrida con lo completado.
    if ui.session_state.get("batch_phase") == "running":
        _run_batch_step(g)
    elif ui.button("Ejecutar suite", key=f"batch_run_{g}"):
        runtime = _build_runtime()
        if runtime is None:
            return
        config, client, evaluator = runtime
        ui.session_state["batch_phase"] = "running"
        ui.session_state["batch_pending"] = list(loaded.cases)
        ui.session_state["batch_done"] = []
        ui.session_state["batch_total"] = len(loaded.cases)
        ui.session_state["batch_agent_id"] = config.agent_id
        ui.session_state["batch_traces"] = fetch_traces
        ui.session_state["batch_client"] = client
        ui.session_state["batch_evaluator"] = evaluator
        ui.session_state.pop("batch_result", None)
        ui.rerun()

    batch_data = ui.session_state.get("batch_result")
    if batch_data is not None:
        _render_batch_result(cast("dict[str, object]", batch_data))


@ui.fragment(run_every=0.4)
def _run_batch_step(g: int) -> None:
    """Ejecuta un caso del lote por tick y cede el control a la interfaz entre casos.

    El `run_every` redibuja periódicamente: entre casos el navegador puede enviar el
    click de "Frenar" (SPEC-006 FR-US3-003). Un click dispara un rerun inmediato del
    fragment, así la parada se atiende sin esperar al tick. El caso que se está
    ejecutando al momento del click termina y se incluye; los pendientes quedan fuera
    (Streamlit no interrumpe un caso en curso, a diferencia del Ctrl+C del runner).
    """
    if ui.session_state.get("batch_phase") != "running":
        return

    done = cast("list[TestResult]", ui.session_state["batch_done"])
    pending = cast("list[TestCase]", ui.session_state["batch_pending"])
    total = cast(int, ui.session_state["batch_total"])

    ui.progress(
        (len(done) / total) if total else 0.0,
        text=f"{len(done)}/{total} caso(s) completado(s)",
    )
    for r in done:
        ui.markdown(f"- {len(done)}/{total} · `{r.case_id}` → **{r.verdict}**")

    if ui.button("Frenar y guardar lo hecho", key=f"batch_stop_{g}"):
        _finalize_batch(stopped=True)
        ui.rerun()
        return

    if pending:
        case = pending.pop(0)
        client = cast("RemoteAgentClient", ui.session_state["batch_client"])
        evaluator = cast(ClassificationEvaluator, ui.session_state["batch_evaluator"])
        try:
            outcome = run_one(
                case,
                client,
                evaluator,
                capture_trace=bool(ui.session_state["batch_traces"]),
            )
        except Exception as exc:  # un fallo puntual no aborta la corrida (FR-US1-010)
            outcome = execution_failure(case, f"excepción inesperada: {exc}")
        done.append(outcome)
        ui.session_state["batch_done"] = done
        ui.session_state["batch_pending"] = pending
    else:
        _finalize_batch(stopped=False)
        ui.rerun()


def _finalize_batch(*, stopped: bool) -> None:
    """Cierra la corrida con los casos completados y la persiste (SPEC-006 FR-US3-004).

    La corrida parcial es un SuiteResult de longitud K, indistinguible en formato de
    una corrida de K casos. Una parada sin casos completados no persiste un run vacío
    (FR-US3-005). Misma ruta de finalización que el runner headless.
    """
    done = cast("list[TestResult]", ui.session_state.get("batch_done", []))
    total = cast(int, ui.session_state.get("batch_total", len(done)))
    agent_id = cast(str, ui.session_state.get("batch_agent_id", ""))

    ui.session_state["batch_phase"] = "idle"
    for key in ("batch_pending", "batch_client", "batch_evaluator"):
        ui.session_state.pop(key, None)

    if stopped and not done:
        ui.session_state["batch_result"] = {
            "run": SuiteResult.create((), agent_id=agent_id),
            "saved_path": None,
            "stopped": True,
            "requested": total,
            "empty": True,
        }
        return

    suite = SuiteResult.create(tuple(done), agent_id=agent_id)
    saved_path: str | None = None
    persist_error: str | None = None
    try:
        saved_path = FileRunRepository().save(suite)
    except RunPersistenceError as err:
        persist_error = str(err)
    ui.session_state["batch_result"] = {
        "run": suite,
        "saved_path": saved_path,
        "stopped": stopped,
        "requested": total,
        "persist_error": persist_error,
    }


def _render_batch_result(data: dict[str, object]) -> None:
    run = cast(SuiteResult, data["run"])
    saved_path = cast("str | None", data.get("saved_path"))

    stopped = bool(data.get("stopped"))
    requested = cast("int | None", data.get("requested"))
    if data.get("empty"):
        ui.warning("Corrida frenada sin ningún caso completado: no se guardó una corrida vacía.")
        return
    if stopped and requested is not None and run.total < requested:
        ui.warning(
            f"Frenado manual: {run.total} de {requested} caso(s) completado(s). "
            "Los casos restantes no forman parte de la corrida."
        )

    persist_error = cast("str | None", data.get("persist_error"))
    if persist_error:
        ui.error(f"La corrida se cerró pero NO se pudo persistir: {persist_error}")

    s = run.summary
    cols = ui.columns(5)
    cols[0].metric("Total", s["total"])
    cols[1].metric("Pass", s["pass"])
    cols[2].metric("Fail", s["fail"])
    cols[3].metric("Indeterminado", s["indeterminado"])
    bruta = run.accuracy_bruta
    cols[4].metric("Accuracy", "—" if bruta is None else f"{bruta:.0%}")

    ui.markdown("**Detalle por caso:**")
    ui.table(
        [
            {
                "case_id": r.case_id,
                "esperado": r.expected,
                "detectado": r.extracted_classification or "—",
                "veredicto": r.verdict,
            }
            for r in run.results
        ]
    )

    ui.markdown("**Respuesta del agente por caso:**")
    for r in run.results:
        with ui.expander(f"{r.case_id} → {r.verdict}"):
            cols = ui.columns(2)
            cols[0].metric("Esperado", r.expected)
            cols[1].metric("Detectado", r.extracted_classification or "—")
            if r.notes:
                ui.caption(r.notes)
            ui.markdown(r.actual_response or "_(respuesta vacía)_")
            if r.conversation_id:
                ui.caption(f"conversation_id: `{r.conversation_id}`")
            _render_case_trace(r, key_prefix="batch")

    _render_suite_metrics(run)

    if saved_path:
        ui.caption(f"Corrida guardada en: `{saved_path}`")


def _render_suite_metrics(run: SuiteResult) -> None:
    """Métricas de una corrida (SPEC-008). El cómputo vive en domain (FR-004)."""
    _render_metrics_block(compute_suite_metrics(run))


def _render_metrics_block(metrics: SuiteMetrics) -> None:
    """Render puro de una matriz de confusión + accuracy por clase + % sin
    clasificación. No recalcula nada: solo lee los agregados de domain (FR-004)."""
    columnas = (*PALETA_CLASIFICACION, SIN_CLASIFICACION)

    ui.markdown("**Matriz de confusión (fila = esperado, columna = detectado):**")
    ui.table(
        [
            {
                "esperado": esperado,
                **{col: metrics.confusion[esperado][col] for col in columnas},
            }
            for esperado in PALETA_CLASIFICACION
        ]
    )

    ui.markdown("**Accuracy por clase:**")
    ui.table(
        [
            {
                "clase": c,
                "accuracy": (
                    "N/A"
                    if metrics.accuracy_por_clase[c] is None
                    else f"{metrics.accuracy_por_clase[c]:.0%}"
                ),
            }
            for c in PALETA_CLASIFICACION
        ]
    )

    ratio = metrics.sin_clasificacion_ratio
    ui.caption(
        f"Sin clasificación extraíble: {metrics.sin_clasificacion_count}/{metrics.total}"
        + ("" if ratio is None else f" ({ratio:.1%})")
    )


def _render_case_trace(r: TestResult, key_prefix: str) -> None:
    """Traza por caso de un run batch (SPEC-010 US1): flow_id como ancla + traza
    persistida a pedido. Sin expander anidado (Streamlit no lo permite) ni botón
    de refresco (el re-fetch por recencia no es válido en batch, FR-US2-007).

    `key_prefix` distingue el contexto de render (corrida en memoria vs. corrida
    guardada), que pueden mostrar el mismo `case_id` en la misma página: sin el
    prefijo las claves de los widgets colisionarían."""
    if r.trace is None:
        ui.caption("Traza no disponible para este caso.")
        return
    ui.caption(f"flow_id: `{r.trace.flow_id or '—'}`")
    if ui.checkbox("Mostrar traza de ejecución", key=f"{key_prefix}_trace_{r.case_id}"):
        render_trace(r.trace)
        if r.trace.overall_status not in ("completed", "failed"):
            ui.caption(
                "El flow seguía cerrando tareas internas cuando se capturó la traza "
                f"(estado: {r.trace.overall_status}). El veredicto no cambia; el cierre "
                "completo se consulta abriendo el flow en la plataforma por su flow_id."
            )


def _render_run_stats_control() -> None:
    """Botón que genera estadistica-corridas.csv a pedido, sin re-ejecutar (US2)."""
    ui.caption(
        "Genera `estadistica-corridas.csv` con una fila por corrida (accuracy incluido) "
        "a partir de todas las corridas guardadas en `runs/detail/` (simple y batch). "
        "No vuelve a llamar al agente."
    )
    if ui.button("Generar estadística de corridas"):
        repo = FileRunRepository()
        try:
            path = repo.regenerate_run_stats()
        except RunPersistenceError as err:
            ui.error(f"No se pudo generar la estadística: {err}")
            return
        ui.success(f"Estadística de corridas regenerada en: `{path}`")

        runs = repo.load_all()
        overall = aggregate_runs(runs)
        ui.markdown("**Total general (todos los casos de todas las corridas):**")
        cols = ui.columns(4)
        cols[0].metric("Casos", overall.total)
        cols[1].metric("Pass", overall.passed)
        cols[2].metric("Fail", overall.failed)
        cols[3].metric("Indeterminado", overall.indeterminate)
        ab = overall.accuracy_bruta
        ae = overall.accuracy_efectiva
        ui.caption(
            f"Accuracy bruta: {'—' if ab is None else f'{ab:.1%}'} · "
            f"Accuracy efectiva: {'—' if ae is None else f'{ae:.1%}'}"
        )
        ui.caption(
            "Para la matriz de confusión general (todos los casos de todas las "
            "corridas) elegí «Todas las corridas» en «Revisar una corrida guardada»."
        )


def _reset_case() -> None:
    g = ui.session_state.get("form_gen", 0)
    for key in (f"file_upload_{g}", f"file_clasif_{g}", f"file_confirm_{g}"):
        ui.session_state.pop(key, None)
    ui.session_state.pop("case_validated", None)
    ui.session_state.pop("eval_result", None)
    _clear_batch_run_state(ui.session_state)
    ui.session_state.pop("batch_file_key", None)
    ui.session_state["form_gen"] = g + 1
    ui.session_state["nav_top"] = True
    ui.rerun()


def _file_needs_clasificacion(raw: bytes) -> bool:
    """True when the file is parseable JSON but lacks clasificacion_esperada at root."""
    import json as _json  # local import: only needed for dashboard file-load path

    try:
        data = _json.loads(raw)
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    return not bool(data.get("clasificacion_esperada", ""))


def _inject_clasificacion(raw: bytes, clasificacion: str) -> bytes:
    import json as _json  # local import: only needed for dashboard file-load path

    data = _json.loads(raw)
    if isinstance(data, dict):
        data["clasificacion_esperada"] = clasificacion
    return _json.dumps(data).encode()


def _load_and_store(raw: bytes) -> None:
    try:
        case = load_case(raw)
        ui.session_state["case_validated"] = case
        ui.success(f"Caso '{case.id}' cargado desde archivo.")
    except CaseLoadError as err:
        ui.error(f"Error de formato: {err}")
    except ValueError as err:
        ui.error(f"Validacion fallida: {err}")


def main() -> None:
    ui.set_page_config(page_title="Pruebas — Agente de atención de intents", layout="wide")

    ui.markdown('<a name="inicio"></a>', unsafe_allow_html=True)

    if ui.session_state.pop("nav_top", False):
        ui.components.v1.html(
            "<script>"
            "setTimeout(function(){"
            "var a=window.parent.document.querySelector('a[name=\"inicio\"]');"
            "if(a)a.scrollIntoView();"
            "},300);"
            "</script>",
            height=0,
        )

    _col_title, _col_btn = ui.columns([8, 2])
    with _col_title:
        ui.title("Dashboard de pruebas — Agente de atención de intents")
        ui.caption(
            "Cargá un caso (o un lote), enviálo al agente bajo prueba y compará su "
            "clasificación de riesgo contra el resultado esperado."
        )
    with _col_btn:
        if ui.session_state.get("case_validated") is not None and ui.button(
            "Limpiar y Evaluar otro caso", key="reset_top"
        ):
            _reset_case()

    g: int = ui.session_state.get("form_gen", 0)

    with ui.expander("Evaluación en lote (varios casos desde archivo)", expanded=False):
        _render_batch(g)

    with ui.expander("Revisar una corrida guardada (sin re-ejecutar)", expanded=False):
        _render_latest_run()

    with ui.expander("Estadísticas y accuracy entre corridas", expanded=False):
        _render_run_stats_control()

    with ui.expander("Cargar un caso desde archivo JSON", expanded=False):
        uploaded = ui.file_uploader(
            "Sube un archivo JSON con los campos del caso",
            type=["json"],
            key=f"file_upload_{g}",
        )
        if uploaded is not None and ui.session_state.get("case_validated") is None:
            raw = uploaded.read()
            needs_clasif = _file_needs_clasificacion(raw)
            if needs_clasif:
                ui.info(
                    "El archivo no incluye 'clasificacion_esperada' (campo de ground truth). "
                    "Seleccionala para continuar:"
                )
                clasif_sel = ui.selectbox(
                    "Clasificacion esperada",
                    list(PALETA_CLASIFICACION),
                    key=f"file_clasif_{g}",
                )
                confirmed = ui.button("Cargar caso", key=f"file_confirm_{g}")
                if confirmed:
                    raw = _inject_clasificacion(raw, clasif_sel)
                    _load_and_store(raw)
            else:
                _load_and_store(raw)

    ui.subheader("Evaluar un caso individual")
    with ui.form(f"single_case_form_{g}", clear_on_submit=False):
        case_id, nombre = _render_identificacion(g)
        intent = _render_intent(g)
        declaracion = _render_declaracion(g)
        datos = _render_datos(g)
        contexto = _render_contexto_extra(g)
        clasificacion, marcadores = _render_esperado(g)
        validate = ui.form_submit_button("Validar caso")

    if validate:
        try:
            case = _build_case(
                case_id=case_id,
                nombre=nombre,
                intent=intent,
                declaracion=declaracion,
                datos=datos,
                contexto=contexto,
                clasificacion=clasificacion,
                marcadores=marcadores,
            )
        except ValueError as err:
            ui.error(f"Validacion fallida: {err}")
            return
        ui.session_state["case_validated"] = case
        ui.success("Caso valido. Ya podes enviarlo al agente.")

    stored = ui.session_state.get("case_validated")
    if stored is None:
        return
    ready_case = cast(TestCase, stored)

    ui.divider()
    ui.subheader("Envío al agente y evaluación")

    ui.markdown("**Datos que se envían al agente:**")
    ui.json(message_builder.build(ready_case))
    ui.markdown("**Resultado esperado (no se envía, se usa para comparar):**")
    ui.json(ready_case.expected())

    fetch_trace_single = ui.checkbox(
        "Capturar traza de ejecución (una llamada extra al agente)",
        value=False,
        key=f"single_trace_{g}",
    )

    if ui.button("Enviar al agente"):
        _send_and_evaluate(ready_case, fetch_trace=fetch_trace_single)

    eval_data = ui.session_state.get("eval_result")
    if eval_data is not None:
        _render_eval_result(eval_data)
        ui.divider()
        if ui.button("Limpiar y Evaluar otro caso", key="reset_bottom"):
            _reset_case()


if __name__ == "__main__":
    main()
