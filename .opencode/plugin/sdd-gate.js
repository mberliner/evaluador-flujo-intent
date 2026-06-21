// SDD gate para opencode — paridad con el hook PreToolUse de Claude Code.
//
// Intercepta las tools `edit` y `write` ANTES de ejecutarse y delega la
// decision en `tools/sdd_gate.py` (SSOT agnostico de asistente, transporte
// argv). Si el gate devuelve exit 2, lanza para abortar la edicion y propaga
// el motivo al asistente. Backstop a posteriori: pre-commit + pipeline_local.
//
// Sin imports de @opencode-ai/plugin: opencode inyecta el runtime y este
// archivo se versiona (a diferencia de node_modules/, ver .opencode/.gitignore).
//
// Wiring del lado Claude: .claude/settings.json (stdin JSON). Ver
// docs/SDD-ENFORCEMENT.md (Principio V).

import fs from "node:fs"
import path from "node:path"

export const SddGate = async ({ directory, $ }) => {
  const root = directory
  const gate = path.join(root, "tools", "sdd_gate.py")
  const candidates = [
    path.join(root, ".venv", "bin", "python"),
    path.join(root, ".venv", "Scripts", "python.exe"),
  ]
  const py = candidates.find((p) => fs.existsSync(p)) ?? "python3"

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "edit" && input.tool !== "write") return
      const filePath = output?.args?.filePath
      if (!filePath || !fs.existsSync(gate)) return

      const res = await $`${py} ${gate} ${filePath}`.cwd(root).nothrow().quiet()
      if (res.exitCode === 2) {
        const reason = res.stderr.toString().trim()
        throw new Error(
          reason || "sdd-gate: edicion de src/ bloqueada (Principio V).",
        )
      }
    },
  }
}
