from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from .cli import run
import os, pathlib, hashlib, sys, traceback

VERSION = "ui-check-v15"  # shows on /healthz

app = FastAPI(title=f"Insta Scrapper API {VERSION}")

@app.on_event("startup")
async def write_storage_state():
    try:
        s = os.getenv("STORAGE_STATE_JSON")
        if s:
            with open("storage_state.json", "w", encoding="utf-8") as f:
                f.write(s)
    except Exception as e:
        print("WARN: could not write STORAGE_STATE_JSON:", e, file=sys.stderr)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok-" + VERSION

@app.get("/__whoami")
def whoami():
    return {"module": "app.webapi", "version": VERSION}

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Insta Scrapper</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root { --bg:#0d0a07; --panel:#16120f; --accent:#ff7a00; --accent2:#ffb86b; --text:#fefaf5; --border:#2a1d14; }
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(180deg,#0b0705,#1a120d 70%);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:var(--text)}
  .wrap{max-width:900px;margin:32px auto;padding:0 16px}
  h1{margin:0 0 10px;font-size:38px;background:linear-gradient(90deg,var(--accent),var(--accent2));
     -webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .panel{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:16px}
  form{display:flex;gap:10px;flex-wrap:wrap}
  input{flex:1;min-width:260px;background:#120c08;color:var(--text);border:1px solid var(--border);border-radius:10px;padding:12px 14px;outline:none}
  button{background:var(--accent);color:#1a120d;font-weight:600;border:0;border-radius:10px;padding:12px 16px;cursor:pointer}
  .secondary{background:#24170f;color:#fff;border:1px solid var(--border)}
  pre{background:#111827;color:#e5e7eb;border:1px solid var(--border);border-radius:12px;padding:12px;white-space:pre-wrap}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Insta Scrapper</h1>
    <div class="panel">
      <form id="f">
        <input id="u" placeholder="public username e.g. espncricinfo" required />
        <button type="submit">Scrape</button>
        <button id="dlJson" type="button" class="secondary" disabled>Download JSON</button>
        <button id="dlTxt"  type="button" class="secondary" disabled>Download TXT</button>
      </form>
      <div id="status" style="color:#cbb9a8;margin:10px 0 8px">Ready (v15).</div>
      <pre id="out" style="min-height:80px">No data yet.</pre>
    </div>
  </div>
<script>
const f=document.getElementById('f');
const u=document.getElementById('u');
const out=document.getElementById('out');
const statusEl=document.getElementById('status');
const btnJ=document.getElementById('dlJson');
const btnT=document.getElementById('dlTxt');
let last=null;
function setStatus(t){ statusEl.textContent=t; }
f.addEventListener('submit', async (e)=>{
  e.preventDefault();
  setStatus('Scraping…'); out.textContent='Loading…'; btnJ.disabled=true; btnT.disabled=true;
  try{
    const res = await fetch('/profile?username=' + encodeURIComponent(u.value));
    const data = await res.json(); last = data;
    out.textContent = JSON.stringify(data, null, 2);
    setStatus(data.ok ? 'Done.' : ('Failed: ' + (data.error||'unknown error')));
    if (data.ok){ btnJ.disabled=false; btnT.disabled=false; }
  }catch(err){
    setStatus('Request failed: '+err); out.textContent = String(err);
  }
});
btnJ.addEventListener('click', ()=>{
  if(!last) return;
  const blob = new Blob([JSON.stringify(last,null,2)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = (last.username||'profile') + '_profile.json';
  a.click(); URL.revokeObjectURL(a.href);
});
btnT.addEventListener('click', ()=>{
  if(!last) return;
  function N(v){return (v==null)?'-':(Number(v)).toLocaleString();}
  const lines = [
    'Name: ' + (last.name||'-'),
    'Username: @' + (last.username||'-'),
    'Bio: ' + (last.bio||'-'),
    'Followers: ' + N(last.followers),
    'Following: ' + N(last.following),
    'Posts: ' + N(last.posts),
    'Profile: ' + (last.profile_url||'-')
  ];
  const blob = new Blob([lines.join('\\n')], {type:'text/plain'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = (last.username||'profile') + '_profile.txt';
  a.click(); URL.revokeObjectURL(a.href);
});
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@app.get("/profile")
async def profile(username: str, query: str | None = None):
    try:
        data = await run(query=query, username=username, headless=True)
        return JSONResponse(data)
    except Exception as e:
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("ERROR /profile\\n", tb, file=sys.stderr, flush=True)
        return JSONResponse({"ok": False, "error": str(e), "trace": tb[-2000:]}, status_code=500)

@app.get("/profile.txt", response_class=PlainTextResponse)
async def profile_txt(username: str):
    data = await run(query=None, username=username, headless=True)
    if not data or not data.get("ok"):
        return PlainTextResponse(str(data), status_code=500)
    def num(v): return "-" if v is None else f"{v:,}"
    lines = [
        f"Name: {data.get('name') or '-'}",
        f"Username: @{data.get('username')}",
        f"Bio: {data.get('bio') or '-'}",
        f"Followers: {num(data.get('followers'))}",
        f"Following: {num(data.get('following'))}",
        f"Posts: {num(data.get('posts'))}",
        f"Profile: {data.get('profile_url')}",
    ]
    return "\\n".join(lines)

def _sha256_prefix(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

@app.get("/debug/storage")
def debug_storage():
    env = os.getenv("STORAGE_STATE_JSON")
    return {
        "env_present": env is not None,
        "env_len": len(env) if env else 0,
        "file_exists": os.path.exists("storage_state.json"),
        "file_size": os.path.getsize("storage_state.json") if os.path.exists("storage_state.json") else 0,
        "file_sha256_prefix": _sha256_prefix("storage_state.json"),
    }

@app.get("/debug/code")
def debug_code():
    b = pathlib.Path("app/browser.py").read_text(encoding="utf-8", errors="ignore")
    c = pathlib.Path("app/cli.py").read_text(encoding="utf-8", errors="ignore")
    combined = b + c
    return {
        "browser_has_fallback": "os.path.exists(storage_state_path)" in b,
        "cli_uses_optional": ('os.path.exists("storage_state.json")' in c) or ("os.path.exists('storage_state.json')" in c),
        "any_direct_open_calls": ('open("storage_state.json"' in combined) or ("open('storage_state.json'" in combined),
    }
