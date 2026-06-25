// SDD gate para opencode — paridad con el hook PreToolUse de Claude Code.
//
// Intercepta las tools de ESCRITURA (edit, write, multiedit, apply_patch y
// cualquier variante de patch) ANTES de ejecutarse, extrae todas las rutas que
// tocarian y delega la decision en `tools/sdd_gate.py` (SSOT agnostico de
// asistente, transporte argv) por cada ruta bajo `src/`. Contrato del gate:
// exit 0 = permitir, exit 2 = bloquear (stderr lleva el motivo). Cualquier otro
// exit significa que el gate NO llego a correr (interprete ausente/roto): es
// FAIL-CLOSED, se bloquea. Backstop universal a posteriori (cubre tools no
// interceptadas aqui): pre-commit + pipeline_local.
//
// Sin imports de @opencode-ai/plugin: opencode inyecta el runtime y este
// archivo se versiona (a diferencia de node_modules/, ver .opencode/.gitignore).
//
// Wiring del lado Claude: .claude/settings.json (stdin JSON). Ver
// docs/SDD-ENFORCEMENT.md (Principio V).

import fs from "node:fs"
import path from "node:path"

// Tools que pueden escribir archivos. Enganchar por nombre es una allowlist
// (las tools de lectura no deben disparar el gate); pre-commit es la red para
// tools de escritura no contempladas aqui. `includes("patch")` cubre variantes.
const isWriteTool = (tool) => {
  const t = String(tool ?? "").toLowerCase()
  return (
    t === "edit" ||
    t === "write" ||
    t === "multiedit" ||
    t.includes("patch")
  )
}

// Rutas declaradas en un patch estilo Codex (apply_patch): cabeceras
// `*** Add|Update|Delete File: <ruta>` y `*** Move to: <ruta>`.
const PATCH_FILE_RE = /^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$/gim
const PATCH_MOVE_RE = /^\*\*\*\s+Move to:\s*(.+?)\s*$/gim

// Recolecta todos los valores string de `args` (recursivo) — el texto del patch
// vive en alguno de ellos y no asumimos el nombre del campo (`args` es `any`).
const collectStrings = (val, out) => {
  if (typeof val === "string") out.push(val)
  else if (Array.isArray(val)) val.forEach((v) => collectStrings(v, out))
  else if (val && typeof val === "object")
    Object.values(val).forEach((v) => collectStrings(v, out))
}

// Recolecta valores de claves de ruta conocidas (filePath/file_path/path) en
// cualquier nivel — cubre edit/write sin asumir profundidad del shape.
const collectKeyedPaths = (val, out) => {
  if (Array.isArray(val)) {
    val.forEach((v) => collectKeyedPaths(v, out))
  } else if (val && typeof val === "object") {
    for (const [k, v] of Object.entries(val)) {
      if (typeof v === "string" && /^(filePath|file_path|path)$/.test(k))
        out.push(v)
      else collectKeyedPaths(v, out)
    }
  }
}

// Todas las rutas que la tool tocaria, sin duplicar. La ruta puede llegar en
// `input.args` (shape real del runtime) o `output.args` (lo que sugieren los
// tipos .d.ts); leemos de ambos por robustez ante variaciones de version.
const collectPaths = (input, output) => {
  const args = input?.args ?? output?.args ?? {}
  const paths = new Set()
  const keyed = []
  collectKeyedPaths(args, keyed)
  keyed.forEach((p) => paths.add(p))
  const strings = []
  collectStrings(args, strings)
  for (const s of strings) {
    for (const re of [PATCH_FILE_RE, PATCH_MOVE_RE]) {
      re.lastIndex = 0
      let m
      while ((m = re.exec(s))) paths.add(m[1])
    }
  }
  return [...paths]
}

// ¿La ruta absoluta cae dentro de `<root>/src/`?
const isUnderSrc = (root, abs) => {
  const rel = path.relative(root, abs)
  if (rel.startsWith("..") || path.isAbsolute(rel)) return false
  return rel === "src" || rel.startsWith("src" + path.sep)
}

// Resuelve una ruta de tool a su ABSOLUTA bajo `src/`, o null si no toca `src/`.
// Pre-filtro barato (no la politica spec-first, SSOT de tools/sdd_gate.py) para
// no depender de Python fuera de `src/`. Devolver la absoluta es necesario: el
// gate tambien resuelve contra el root, asi que una relativa como `dummy.py`
// (apply_patch lanzado con cwd dentro de src/) se le escaparia.
//
// Las rutas del patch son relativas al cwd de la tool, que la API de opencode
// NO expone al hook (`tool.execute.before` solo trae tool/sessionID/callID).
// Heuristica: si la relativa no cae en src/ contra el root pero SI existe al
// resolverla bajo src/, asumimos que el cwd estaba dentro de src/. Cubre
// edit/move/delete sobre archivos existentes; la *creacion* de un archivo nuevo
// en src/ con cwd interno a src/ no es determinista aqui y la cubre pre-commit.
const resolveSrcPath = (root, p) => {
  const direct = path.resolve(root, p)
  if (isUnderSrc(root, direct)) return direct
  if (!path.isAbsolute(p)) {
    const underSrc = path.resolve(root, "src", p)
    if (isUnderSrc(root, underSrc) && fs.existsSync(underSrc)) return underSrc
  }
  return null
}

export const SddGate = async ({ directory, $ }) => {
  const root = directory
  const gate = path.join(root, "tools", "sdd_gate.py")
  // Orden de preferencia: venv del proyecto, luego python/python3 del PATH.
  // Los del venv se filtran por existencia; los del PATH se prueban al ejecutar
  // (un exit != 0 y != 2 los descarta y pasa al siguiente).
  const candidates = [
    path.join(root, ".venv", "Scripts", "python.exe"),
    path.join(root, ".venv", "bin", "python"),
    "python",
    "python3",
  ]

  // Corre el gate sobre una ruta. Lanza si el gate bloquea (exit 2) o si ningun
  // interprete logra ejecutarlo (fail-closed). Retorna si el gate permite.
  const runGate = async (filePath) => {
    let lastDetail = "ningun interprete de Python disponible"
    for (const py of candidates) {
      if (path.isAbsolute(py) && !fs.existsSync(py)) continue
      const res = await $`${py} ${gate} ${filePath}`.cwd(root).nothrow().quiet()
      if (res.exitCode === 0) return // el gate corrio y permitio
      if (res.exitCode === 2) {
        const reason = res.stderr.toString().trim()
        throw new Error(
          reason || "sdd-gate: edicion de src/ bloqueada (Principio V).",
        )
      }
      // exit != 0 y != 2: el gate no llego a ejecutarse con este interprete.
      lastDetail = `${py} -> exit ${res.exitCode}: ${res.stderr.toString().trim()}`
    }
    throw new Error(
      "sdd-gate: no se pudo ejecutar tools/sdd_gate.py, edicion de src/ " +
        "bloqueada por seguridad (Principio V). Crea el .venv del proyecto o " +
        "instala Python en el PATH. Detalle: " +
        lastDetail,
    )
  }

  return {
    "tool.execute.before": async (input, output) => {
      if (!isWriteTool(input?.tool)) return
      if (!fs.existsSync(gate)) return
      const srcPaths = new Set()
      for (const p of collectPaths(input, output)) {
        const abs = resolveSrcPath(root, p)
        if (abs) srcPaths.add(abs)
      }
      for (const p of srcPaths) await runGate(p)
    },
  }
}
