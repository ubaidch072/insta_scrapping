<<<<<<< HEAD
ï»¿from fastapi import FastAPI
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

=======
# app/webapi.py
# ------------------------------------------------------------
# FastAPI app + embedded UI for Instagram scraping.
# - Windows asyncio fix => WindowsSelectorEventLoopPolicy (required for Playwright)
# - STORAGE_STATE_JSON -> storage_state.json on startup
# - Safer JS (bind after DOM ready)
# - Buttons: Scrape, View Recent Posts, Download JSON, Download TXT, Exit
# - Debug: /healthz, /__whoami, /debug/storage, /debug/code, /debug/loop
# ------------------------------------------------------------

# --- Windows asyncio fix (KEEP FIRST) ---
import sys, asyncio, os, pathlib, hashlib, traceback

def _ensure_selector_policy():
    """Force Windows Selector loop (Playwright needs subprocess support)."""
    if sys.platform.startswith("win"):
        try:
            pol = asyncio.get_event_loop_policy()
            proactor = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
            selector = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
            if selector and (proactor and isinstance(pol, proactor) or type(pol).__name__ == "WindowsProactorEventLoopPolicy"):
                asyncio.set_event_loop_policy(selector())
        except Exception:
            pass

_ensure_selector_policy()
# ---------------------------------------

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .cli import run

VERSION = "ui-check-v21"
DEBUG_ERRORS = os.getenv("DEBUG_ERRORS") == "1"
MOCK = os.getenv("MOCK") == "1"

app = FastAPI(title=f"Insta Scrapper API {VERSION}")

# ---------- write cookies from env (optional) ----------
@app.on_event("startup")
async def write_storage_state() -> None:
    try:
        s = os.getenv("STORAGE_STATE_JSON")
        if s:
            pathlib.Path("storage_state.json").write_text(s, encoding="utf-8")
    except Exception:
        pass

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health / whoami / loop ----------
@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok-" + VERSION

>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
@app.get("/__whoami")
def whoami():
    return {"module": "app.webapi", "version": VERSION}

<<<<<<< HEAD
HTML = """
=======
@app.get("/debug/loop")
def debug_loop():
    loop = asyncio.get_event_loop()
    pol = asyncio.get_event_loop_policy()
    return {"policy": type(pol).__name__, "loop": type(loop).__name__}

# ---------- UI (NOT an f-string!) ----------
HTML_TMPL = """
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Insta Scrapper</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
<<<<<<< HEAD
  :root { --bg:#0d0a07; --panel:#16120f; --accent:#ff7a00; --accent2:#ffb86b; --text:#fefaf5; --border:#2a1d14; }
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(180deg,#0b0705,#1a120d 70%);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:var(--text)}
  .wrap{max-width:900px;margin:32px auto;padding:0 16px}
=======
  :root { --bg:#0d0a07; --panel:#16120f; --accent:#ff7a00; --accent2:#ffb86b;
          --text:#fefaf5; --muted:#cbb9a8; --border:#2a1d14; }
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(180deg,#0b0705,#1a120d 70%);
       font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:var(--text)}
  .wrap{max-width:1000px;margin:32px auto;padding:0 16px}
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
  h1{margin:0 0 10px;font-size:38px;background:linear-gradient(90deg,var(--accent),var(--accent2));
     -webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .panel{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:16px}
  form{display:flex;gap:10px;flex-wrap:wrap}
<<<<<<< HEAD
  input{flex:1;min-width:260px;background:#120c08;color:var(--text);border:1px solid var(--border);border-radius:10px;padding:12px 14px;outline:none}
  button{background:var(--accent);color:#1a120d;font-weight:600;border:0;border-radius:10px;padding:12px 16px;cursor:pointer}
  .secondary{background:#24170f;color:#fff;border:1px solid var(--border)}
  pre{background:#111827;color:#e5e7eb;border:1px solid var(--border);border-radius:12px;padding:12px;white-space:pre-wrap}
=======
  input{flex:1;min-width:260px;background:#120c08;color:var(--text);border:1px solid var(--border);
        border-radius:10px;padding:12px 14px;outline:none}
  button{background:var(--accent);color:#1a120d;font-weight:600;border:0;border-radius:10px;padding:12px 16px;cursor:pointer}
  .secondary{background:#24170f;color:var(--text);border:1px solid var(--border)}
  pre{background:#111827;color:#e5e7eb;border:1px solid var(--border);border-radius:12px;padding:12px;white-space:pre-wrap}
  label{color:#cbb9a8}
  .footer{display:flex;justify-content:flex-end;margin-top:12px}
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
</style>
</head>
<body>
  <div class="wrap">
    <h1>Insta Scrapper</h1>
    <div class="panel">
      <form id="f">
        <input id="u" placeholder="public username e.g. espncricinfo" required />
<<<<<<< HEAD
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
  setStatus('Scrapingâ€¦'); out.textContent='Loadingâ€¦'; btnJ.disabled=true; btnT.disabled=true;
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
=======
        <button id="btnScrape" type="submit">Scrape</button>
        <button id="viewPosts" type="button" class="secondary" disabled>View Recent Posts</button>
        <button id="dlJson" type="button" class="secondary" disabled>Download JSON</button>
        <button id="dlTxt"  type="button" class="secondary" disabled>Download TXT</button>
      </form>

      <div id="status" style="color:#cbb9a8;margin:10px 0 8px">Ready ({VERSION}).</div>
      <pre id="out" style="min-height:80px">No data yet.</pre>

      <!-- posts gallery -->
      <div id="gallery" style="display:none;margin-top:12px" class="panel">
        <h3 style="margin:0 0 8px">Recent Posts</h3>
        <div id="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;"></div>
      </div>

      <div class="footer">
        <button id="exitApp" type="button" class="secondary">Exit</button>
      </div>
    </div>
  </div>

<!-- Safer JS: bind after DOM ready -->
<script>
(function(){
  function ready(fn){ if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(() => {
    const f = document.getElementById('f');
    const u = document.getElementById('u');
    const out = document.getElementById('out');
    const statusEl = document.getElementById('status');
    const btnJ = document.getElementById('dlJson');
    const btnT = document.getElementById('dlTxt');
    const btnV = document.getElementById('viewPosts');
    const btnExit = document.getElementById('exitApp');
    const gallery = document.getElementById('gallery');
    const grid = document.getElementById('grid');
    let last = null;

    function setStatus(t){ statusEl.textContent = t; }

    function renderGallery(data){
      grid.innerHTML='';
      if(!data.posts_data || data.posts_data.length===0){
        grid.innerHTML = '<div style="color:#cbb9a8">No posts to show.</div>';
      } else {
        for(const p of data.posts_data){
          const card = document.createElement('div');
          card.className = 'panel';
          card.style.padding='10px';
          const cap = (p.caption||'').replace(/\\s+/g,' ').trim();
          const date = p.posted_at ? new Date(p.posted_at).toLocaleString() : '';
          const media = (p.media_urls && p.media_urls.length>0) ? p.media_urls[0] : null;

          let mediaHtml = '';
          if(media){
            if(/\\.(mp4|webm)(\\?|$)/i.test(media) || (media||'').includes('video')){
              mediaHtml = `<video src="${media}" controls style="width:100%;border-radius:10px"></video>`;
            } else {
              mediaHtml = `<img src="${media}" alt="" style="width:100%;border-radius:10px;display:block" />`;
            }
          } else {
            mediaHtml = `<div style="color:#cbb9a8">No preview</div>`;
          }

          card.innerHTML = `
            <a href="${p.url}" target="_blank" style="text-decoration:none;color:#ffb86b">Open post â†—</a>
            <div style="margin:6px 0">${mediaHtml}</div>
            <div style="font-size:13px;color:#cbb9a8">${date}</div>
            <div style="margin-top:6px">${cap || '<span style="color:#cbb9a8">No caption</span>'}</div>
          `;
          grid.appendChild(card);
        }
      }
      gallery.style.display='block';
    }

    // View Recent Posts
    btnV.addEventListener('click', () => { if (last) renderGallery(last); });

    // Scrape
    f.addEventListener('submit', async (e)=>{
      e.preventDefault();
      setStatus('Scrapingâ€¦');
      out.textContent='Loadingâ€¦';
      btnJ.disabled=true; btnT.disabled=true; btnV.disabled=true;
      gallery.style.display='none';
      try{
        const res = await fetch('/profile?username=' + encodeURIComponent(u.value));
        const data = await res.json();
        last = data;
        out.textContent = JSON.stringify(data, null, 2);
        setStatus(data.ok ? 'Done.' : ('Failed: ' + (data.error || data.message || 'unknown error')));

        if (data.ok){
          // Enable downloads
          btnJ.disabled=false; btnT.disabled=false;
          // Always enable "View Recent Posts" â€” gallery will show message if empty
          btnV.disabled = false;
          // Optional: auto open gallery if posts found
          if (data.posts_data && data.posts_data.length) { renderGallery(data); }
        }
      }catch(err){
        console.error(err);
        setStatus('Request failed: '+err);
        out.textContent = String(err);
      }
    });

    // Download JSON
    btnJ.addEventListener('click', ()=>{
      if(!last){ alert('No data. Click Scrape first.'); return; }
      const blob = new Blob([JSON.stringify(last,null,2)], {type:'application/json'});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = (last.username||'profile') + '_profile.json';
      a.click(); URL.revokeObjectURL(a.href);
    });

    // Download TXT
    btnT.addEventListener('click', ()=>{
      if(!last){ alert('No data. Click Scrape first.'); return; }
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
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = (last.username||'profile') + '_profile.txt';
      a.click(); URL.revokeObjectURL(a.href);
    });

    // Exit (shutdown backend)
    btnExit.addEventListener('click', async ()=>{
      if(!confirm('Close server?')) return;
      try{
        await fetch('/__shutdown', {method:'POST'});
      }catch(e){}
      setStatus('Shutting downâ€¦');
      setTimeout(()=>{ window.close(); }, 400);
    });

  }); // ready
})();
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
<<<<<<< HEAD
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
=======
    return HTML_TMPL.replace("{VERSION}", VERSION)

# ---------- API ----------
@app.get("/profile")
async def profile(username: str, query: str | None = None):
    # Safety: enforce Selector policy right before running Playwright
    _ensure_selector_policy()
    try:
        if MOCK:
            return JSONResponse({
                "ok": True,
                "username": username,
                "name": "Demo User",
                "bio": "Mock mode âœ…",
                "external_url": "https://example.com",
                "followers": 12345,
                "following": 67,
                "posts": 3,
                "profile_url": f"https://www.instagram.com/{username}/",
                "posts_data": [
                    {"shortcode":"XYZ1","caption":"Hello","media_urls":["https://picsum.photos/300"],"posted_at":"2024-01-01","url":"https://example.com/1"},
                    {"shortcode":"XYZ2","caption":"World","media_urls":["https://picsum.photos/301"],"posted_at":"2024-01-02","url":"https://example.com/2"},
                    {"shortcode":"XYZ3","caption":"!","media_urls":["https://picsum.photos/302"],"posted_at":"2024-01-03","url":"https://example.com/3"},
                ]
            })

        data = await run(query=query, username=username, headless=True)
        return JSONResponse(data)
    except Exception as e:
        msg = str(e) or e.__class__.__name__
        if DEBUG_ERRORS:
            try:
                msg = msg + " | " + traceback.format_exc().splitlines()[-1]
            except Exception:
                pass
        return JSONResponse({"ok": False, "error": msg}, status_code=500)

@app.get("/profile.txt", response_class=PlainTextResponse)
async def profile_txt(username: str):
    if MOCK:
        lines = [
            "Name: Demo User",
            f"Username: @{username}",
            "Bio: Mock mode âœ…",
            "Followers: 12,345",
            "Following: 67",
            "Posts: 3",
            f"Profile: https://www.instagram.com/{username}/",
        ]
        return "\n".join(lines)

    data = await run(query=None, username=username, headless=True)
    if not data or not data.get("ok"):
        return PlainTextResponse(str(data), status_code=500)

>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
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
<<<<<<< HEAD
    return "\\n".join(lines)

def _sha256_prefix(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
=======
    return "\n".join(lines)

# ---------- Exit / Shutdown ----------
@app.post("/__shutdown")
async def shutdown(request: Request):
    """
    Dev convenience: close the uvicorn process from UI.
    """
    loop = asyncio.get_running_loop()
    # small delay so response can flush
    loop.call_later(0.2, lambda: os._exit(0))
    return {"ok": True, "message": "Shutting down"}

# ---------- Debug helpers ----------
def _sha256_prefix(path: str) -> str | None:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

@app.get("/debug/storage")
def debug_storage():
    env = os.getenv("STORAGE_STATE_JSON")
<<<<<<< HEAD
    return {
        "env_present": env is not None,
        "env_len": len(env) if env else 0,
        "file_exists": os.path.exists("storage_state.json"),
        "file_size": os.path.getsize("storage_state.json") if os.path.exists("storage_state.json") else 0,
=======
    file_exists = os.path.exists("storage_state.json")
    return {
        "env_present": env is not None,
        "env_len": len(env) if env else 0,
        "file_exists": file_exists,
        "file_size": os.path.getsize("storage_state.json") if file_exists else 0,
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
        "file_sha256_prefix": _sha256_prefix("storage_state.json"),
    }

@app.get("/debug/code")
def debug_code():
<<<<<<< HEAD
    b = pathlib.Path("app/browser.py").read_text(encoding="utf-8", errors="ignore")
    c = pathlib.Path("app/cli.py").read_text(encoding="utf-8", errors="ignore")
    combined = b + c
    return {
        "browser_has_fallback": "os.path.exists(storage_state_path)" in b,
        "cli_uses_optional": ('os.path.exists("storage_state.json")' in c) or ("os.path.exists('storage_state.json')" in c),
        "any_direct_open_calls": ('open("storage_state.json"' in combined) or ("open('storage_state.json'" in combined),
=======
    try:
        b = pathlib.Path("app/browser.py").read_text(encoding="utf-8", errors="ignore")
    except Exception:
        b = ""
    try:
        c = pathlib.Path("app/cli.py").read_text(encoding="utf-8", errors="ignore")
    except Exception:
        c = ""
    combined = b + c
    return {
        "browser_has_optional_storage": ("if os.path.exists" in b and "storage_state" in b),
        "any_hardcoded_storage": (
            "storage_state='storage_state.json'" in combined
            or 'storage_state="storage_state.json"' in combined
        ),
>>>>>>> 88fc53e (Update: fixed Selector loop + added View Recent Posts, Exit button, Render deploy files)
    }
