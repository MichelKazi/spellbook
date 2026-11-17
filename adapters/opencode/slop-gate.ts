// Spellbook slop gate for opencode. Rendered by `spellbook install`; edit the source in spellbook/adapters/opencode/.
// Translates opencode tool events into the Claude/Codex hook payload and runs the shared gate script.
import { spawnSync } from "node:child_process";
import type { Plugin } from "@opencode-ai/plugin";

const GATE = "__GATE__";

function gate(payload: Record<string, unknown>): string | undefined {
  const r = spawnSync("python3", [GATE], { input: JSON.stringify(payload), encoding: "utf8", timeout: 30_000 });
  const out = (r.stdout || "").trim();
  if (!out) return undefined;
  try {
    const j = JSON.parse(out);
    return j.hookSpecificOutput?.permissionDecisionReason ?? j.reason;
  } catch {
    return undefined;
  }
}

export const SpellbookSlopGate: Plugin = async ({ directory }) => {
  const pendingPaths = new Map<string, string>();

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash") {
        const reason = gate({
          hook_event_name: "PreToolUse",
          tool_name: "Bash",
          tool_input: { command: output.args?.command ?? "" },
          cwd: directory,
        });
        if (reason) throw new Error(reason);
      }
      if (input.tool === "write" || input.tool === "edit") {
        const path = output.args?.filePath;
        if (typeof path === "string") pendingPaths.set(input.callID, path);
      }
    },
    "tool.execute.after": async (input, output) => {
      const path = pendingPaths.get(input.callID);
      if (!path) return;
      pendingPaths.delete(input.callID);
      const reason = gate({
        hook_event_name: "PostToolUse",
        tool_name: "Write",
        tool_input: { file_path: path },
        cwd: directory,
      });
      if (reason) output.output = `${output.output ?? ""}\n\n${reason}`;
    },
  };
};
