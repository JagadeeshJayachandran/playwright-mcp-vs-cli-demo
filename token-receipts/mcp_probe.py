"""Open a web page through one Playwright MCP release, with no AI model involved, and print what the server sends back.
Usage: python3 mcp_probe.py VERSION [URL] [--json]
  e.g.  python3 mcp_probe.py 0.0.30     (July 2025: the page snapshot comes back inside the reply)
        python3 mcp_probe.py latest     (today: the snapshot is saved to a file and the reply links to it)
Runs `npx -y @playwright/mcp@VERSION --headless --isolated` in the current folder, so run it from an empty folder.
Needs Node.js and Python 3. The URL defaults to https://jagadeeshjayachandran.dev."""
import json, subprocess, sys, time, select, os
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args: sys.exit(__doc__)
ver = args[0]; url = args[1] if len(args) > 1 else "https://jagadeeshjayachandran.dev"; cwd = os.getcwd()
p = subprocess.Popen(["npx", "-y", f"@playwright/mcp@{ver}", "--headless", "--isolated"], cwd=cwd,
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
                     start_new_session=True)
nid = [0]
def rpc(method, params=None, notify=False, timeout=120):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None: msg["params"] = params
    if not notify: nid[0] += 1; msg["id"] = nid[0]
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
    if notify: return None
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([p.stdout], [], [], 1)
        if r:
            line = p.stdout.readline()
            if not line: break
            try: m = json.loads(line)
            except Exception: continue
            if m.get("id") == nid[0]: return m
    raise TimeoutError(method)
def text(m): return "\n".join(c.get("text", "") for c in m.get("result", {}).get("content", []) if c.get("type") == "text")
try:
    rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe", "version": "1"}})
    rpc("notifications/initialized", notify=True)
    tl = rpc("tools/list")["result"]["tools"]
    tl_chars = len(json.dumps(tl))
    nav = rpc("tools/call", {"name": "browser_navigate", "arguments": {"url": url}})
    nt = text(nav); kinds = [c.get("type") for c in nav.get("result", {}).get("content", [])]
    out = dict(version=ver, tools=len(tl), tool_json_chars=tl_chars, navigate_chars=len(nt), navigate_inline_yaml=("```yaml" in nt), navigate_content_types=kinds,
               navigate_head=nt[:240].replace("\n", " | "))
    if "--json" in sys.argv: print(json.dumps(out))
    else:
        print(f"Playwright MCP {ver}: {len(tl)} tools, {tl_chars:,} characters of tool definitions")
        print(f"Opened {url}: the server sent back {len(nt):,} characters")
        print("The page snapshot came back INSIDE the reply" if "```yaml" in nt else "The page snapshot was saved to a file; the reply only links to it")
finally:
    try: os.killpg(p.pid, 9)      # npx, the server and its browser
    except Exception: p.kill()
