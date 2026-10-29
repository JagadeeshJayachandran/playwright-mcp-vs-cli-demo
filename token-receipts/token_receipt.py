"""Token receipt for a Claude Code session: where the tokens and dollars went, call by call.
Reads the session log that Claude Code writes for every session: ~/.claude/projects/<folder>/<session-id>.jsonl
(the folder name is your project path with slashes turned into dashes).

Usage: python3 token_receipt.py SESSION.jsonl [--seg N] [--label NAME] [--simulate-inline TOKENS]
  --seg N               only the turn that started with your Nth typed or pasted prompt (1 = the first)
  --simulate-inline T   what-if: every browser action also returned a T-token page snapshot inside the reply,
                        which is how Playwright MCP behaved before snapshots moved to files
Pass the path in full (it starts with / or ~). A bare folder name starts with "-" and reads as an option.

Prices: Claude Code's rates for claude-opus-5-5, per million tokens. They reproduce Claude Code's own
cost totals to the cent. On another model, change P below."""
import json, sys, argparse, collections
P = dict(inp=4.00, out=20.00, cr=0.20, cw=8.00)          # $ per million tokens
ACTIONS = ("navigate", "click", "type", "select", "press", "hover", "fill", "goto", "open")

ap = argparse.ArgumentParser(); ap.add_argument("f"); ap.add_argument("--seg", type=int); ap.add_argument("--label", default="")
ap.add_argument("--simulate-inline", type=int, default=0); a = ap.parse_args()
rows = [json.loads(l) for l in open(a.f)]
calls = collections.OrderedDict(); seg = 0; res = {}
for r in rows:
    t = r.get("type")
    if t == "user" and not r.get("isMeta"):
        c = r["message"]["content"]
        txt = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if b.get("type") == "text")
        if "pasted_content" in txt or (isinstance(c, str) and not txt.startswith("<")): seg += 1
        if not isinstance(c, str):
            for b in c:
                if b.get("type") == "tool_result":
                    cc = b.get("content"); res[b["tool_use_id"]] = len(cc) if isinstance(cc, str) else sum(len(x.get("text", "")) for x in cc or [] if isinstance(x, dict))
    if t == "assistant" and not r.get("isSidechain") and not r["message"].get("model", "").startswith("claude-haiku"):
        m = r["message"]; d = calls.setdefault(m["id"], dict(seg=seg, u={}, tools=[]))
        d["u"] = m.get("usage") or d["u"]
        for b in m.get("content", []):
            if b.get("type") == "tool_use":
                n = b["name"]; cmd = b.get("input", {}).get("command", "") if n == "Bash" else ""
                d["tools"].append((n, cmd, b["id"]))
C = [d for d in calls.values() if a.seg is None or d["seg"] == a.seg]
if not C: sys.exit(f"No model calls found" + (f" for prompt {a.seg}; this session has {seg} prompt(s)" if a.seg else ""))

def is_action(n, cmd):
    s = (n + " " + cmd).lower()
    return ("playwright" in s) and any(k in s for k in ACTIONS) and "snapshot" not in n
def cost(cs):
    tot = collections.Counter()
    for d in cs:
        u = d["u"]; ctx = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        tot["calls"] += 1; tot["inp"] += u.get("input_tokens", 0); tot["out"] += u.get("output_tokens", 0)
        tot["cw"] += u.get("cache_creation_input_tokens", 0) + d.get("sim_new", 0)
        tot["cr"] += u.get("cache_read_input_tokens", 0) + d.get("sim_old", 0)
        tot["peak"] = max(tot["peak"], ctx + d.get("sim_new", 0) + d.get("sim_old", 0))
    usd = {k: tot[k] * P[k] / 1e6 for k in ("inp", "out", "cr", "cw")}
    return tot, usd
if a.simulate_inline:                     # add T tokens after every browser action, carried to every later call
    carried = 0; pending = 0
    for d in C:
        d["sim_new"], d["sim_old"] = pending, carried; carried += pending; pending = 0
        pending += a.simulate_inline * sum(is_action(n, c) for n, c, _ in d["tools"])
tot, usd = cost(C); total = sum(usd.values())
first = C[0]["u"]; base = first.get("cache_read_input_tokens", 0) + first.get("cache_creation_input_tokens", 0) + first.get("input_tokens", 0)
base_usd = first.get("cache_creation_input_tokens", 0) * P["cw"] / 1e6 + base * P["cr"] / 1e6 * (len(C) - 1) + first.get("cache_read_input_tokens", 0) * P["cr"] / 1e6
last = C[-1]["u"]; end = last.get("input_tokens", 0) + last.get("cache_creation_input_tokens", 0) + last.get("cache_read_input_tokens", 0)
acts = sum(is_action(n, c) for d in C for n, c, _ in d["tools"])
print(f"## {a.label or a.f}" + (f"  (SIMULATED: +{a.simulate_inline:,} tokens inline after each of {acts} browser actions)" if a.simulate_inline else ""))
print(f"API calls {tot['calls']} | browser actions {acts} | context at call 1: {base:,} tokens | at the end: {end + (C[-1].get('sim_old',0)+C[-1].get('sim_new',0)):,} | peak {tot['peak']:,}")
print(f"| part | tokens | $ | share |\n|---|---|---|---|")
for k, name in (("cw", "written to cache (new context)"), ("cr", "re-read from cache (every call)"), ("out", "model output + thinking"), ("inp", "uncached input")):
    print(f"| {name} | {tot[k]:,} | {usd[k]:.3f} | {100*usd[k]/total:.0f}% |")
print(f"| **total** | | **{total:.2f}** | |")
if not a.simulate_inline:
    print(f"Baseline (Claude Code's own prompt, tools, project context = the call-1 context, written once and re-read on every call): ${base_usd:.2f} = {100*base_usd/total:.0f}% of the bill")
    big = sorted(((res.get(i, 0), n, c[:60]) for d in C for n, c, i in d["tools"]), reverse=True)[:3]
    print("Largest tool results (chars): " + "; ".join(f"{s:,} {n}{(': '+c) if c else ''}" for s, n, c in big))
print()
