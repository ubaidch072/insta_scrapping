from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, StreamingResponse
from typing import Any, Dict, List, Optional
from loguru import logger
from pathlib import Path
import io, zipfile, json, datetime

from .cli import run  # our core scraper runner

app = FastAPI(title="Insta Scrapper")

# -------------------------
# Helper: TXT summary
# -------------------------
def _to_txt_safe(profile: Dict[str, Any]) -> str:
    def _clean(x):
        if x is None:
            return "-"
        s = str(x).strip()
        return s if s else "-"

    lines: List[str] = []
    lines.append(f"Username      : {_clean(profile.get('username'))}")
    lines.append(f"Full name     : {_clean(profile.get('full_name'))}")
    lines.append(f"Bio           : {_clean(profile.get('bio'))}")
    lines.append(f"External URL  : {_clean(profile.get('external_url'))}")
    lines.append(f"Followers     : {_clean(profile.get('followers'))}")
    lines.append(f"Following     : {_clean(profile.get('following'))}")
    lines.append(f"Profile Photo : {_clean(profile.get('profile_pic_url'))}")
    lines.append("")
    lines.append("Latest posts:")
    posts = profile.get("latest_posts") or profile.get("posts") or []
    if not posts:
        lines.append("  (none)")
    else:
        for i, p in enumerate(posts, 1):
            caption = (p.get("caption") or "").replace("\r", " ").replace("\n", " ").strip()
            if len(caption) > 180:
                caption = caption[:177] + "..."
            media = p.get("media_urls") or p.get("media") or []
            lines.append(f"  {i}. Shortcode : {_clean(p.get('shortcode'))}")
            lines.append(f"     Date      : {_clean(p.get('posted_at'))}")
            lines.append(f"     Caption   : {_clean(caption)}")
            if media:
                lines.append(f"     Media URLs ({len(media)}):")
                for mu in media[:5]:
                    lines.append(f"       - {mu}")
                if len(media) > 5:
                    lines.append(f"       ... +{len(media) - 5} more")
            shot = p.get("screenshot_path")
            if shot:
                lines.append(f"     Screenshot: {shot}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# -------------------------
# Orange Landing Page UI
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Insta Scrapper</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root{
    --bg:#0f0f10; --card:#17181b; --accent:#ff6a00; --accent2:#ff8c3a; --text:#f4f6f8; --muted:#aeb4bc; --border:#25262a;
  }
  body{margin:0;font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;background:linear-gradient(160deg,#0d0d0e,#121316 60%,#0f0f10);}
  .wrap{max-width:900px;margin:40px auto;padding:0 16px;}
  .brand{display:flex;gap:12px;align-items:center;margin-bottom:16px}
  .logo{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:grid;place-items:center;color:#fff;font-weight:800}
  h1{color:var(--text);margin:0;font-size:28px;letter-spacing:.4px}
  p.sub{color:var(--muted);margin:.25rem 0 1.25rem}
  .card{background:rgba(23,24,27,.9);border:1px solid var(--border);border-radius:18px;padding:18px 18px 12px;backdrop-filter: blur(8px);}
  .row{display:flex;flex-wrap:wrap;gap:12px}
  .field{flex:1 1 260px;display:flex;flex-direction:column;gap:6px}
  label{color:var(--muted);font-size:13px}
  input{padding:12px 14px;border-radius:12px;border:1px solid var(--border);background:#0f1012;color:var(--text);outline:none}
  input:focus{border-color:var(--accent)}
  .actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
  button{border:0;padding:12px 14px;border-radius:12px;color:#fff;cursor:pointer;font-weight:600;letter-spacing:.2px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));}
  button.secondary{background:#222428;color:#e8ebef;border:1px solid var(--border)}
  .small{font-size:12px;color:var(--muted);margin-top:6px}
  .jsonbox{white-space:pre-wrap;background:#0d0e11;border:1px solid var(--border);border-radius:14px;padding:12px;color:#cfe6ff;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;max-height:360px;overflow:auto}
  a{color:#ffd2b3}
</style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="logo">IS</div>
      <div>
        <h1>Insta Scrapper</h1>
        <p class="sub">Type a public Instagram username. Choose what you want to fetch.</p>
      </div>
    </div>

    <div class="card">
      <div class="row">
        <div class="field">
          <label>Username (public)</label>
          <input id="username" placeholder="e.g. mrbeast, nasa, instagram" />
          <div class="small">Note: Uses your stored session (storage_state.json). Private accounts won't work.</div>
        </div>
      </div>
      <div class="actions">
        <button onclick="viewJson()">View JSON</button>
        <button class="secondary" onclick="downloadJson()">Download JSON</button>
        <button class="secondary" onclick="downloadTxt()">Download TXT</button>
        <button class="secondary" onclick="downloadZip()">Download Screenshots ZIP</button>
        <a href="/docs"><button class="secondary" type="button">API Docs</button></a>
        <a href="/healthz"><button class="secondary" type="button">Health</button></a>
      </div>
      <div id="out" class="jsonbox" style="display:none;margin-top:12px;"></div>
    </div>
  </div>

<script>
function val(){return (document.getElementById('username').value||'').trim();}
function viewJson(){
  const u = val(); if(!u){alert('Enter a username');return;}
  const out = document.getElementById('out'); out.style.display='block'; out.textContent='Loading...';
  fetch('/profile?username='+encodeURIComponent(u)).then(r=>r.json()).then(j=>{
    out.textContent = JSON.stringify(j,null,2);
  }).catch(e=>{out.textContent='Error: '+e});
}
function downloadJson(){
  const u = val(); if(!u){alert('Enter a username');return;}
  window.location.href = '/profile.json?username='+encodeURIComponent(u);
}
function downloadTxt(){
  const u = val(); if(!u){alert('Enter a username');return;}
  window.location.href = '/profile.txt?username='+encodeURIComponent(u);
}
function downloadZip(){
  const u = val(); if(!u){alert('Enter a username');return;}
  window.location.href = '/profile.zip?username='+encodeURIComponent(u)+'&max_posts=3';
}
</script>
</body>
</html>
    """

# -------------------------
# Health
# -------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}

# -------------------------
# View JSON (on screen)
# -------------------------
@app.get("/profile")
def profile(username: str, query: Optional[str] = None):
    data = run(query=query, username=username, headless=True)
    return data

# -------------------------
# Download JSON
# -------------------------
@app.get("/profile.json")
def profile_json(username: str):
    data = run(query=None, username=username, headless=True)
    filename = f"{username}.json"
    return JSONResponse(content=data, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

# -------------------------
# Download TXT
# -------------------------
@app.get("/profile.txt", response_class=PlainTextResponse)
def profile_txt(username: str):
    data = run(query=None, username=username, headless=True)
    txt = _to_txt_safe(data)
    filename = f"{username}.txt"
    return PlainTextResponse(txt, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

# -------------------------
# Download ZIP (JSON + per-post screenshots)
# -------------------------
@app.get("/profile.zip")
def profile_zip(username: str, max_posts: int = Query(3, ge=1, le=12)):
    data = run(query=None, username=username, headless=True, capture_post_shots=True, max_posts=max_posts)

    # collect any captured screenshot paths
    shots: List[str] = []
    posts = data.get("latest_posts") or []
    for p in posts:
        sp = p.get("screenshot_path")
        if sp and Path(sp).exists():
            shots.append(sp)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt",
                    f"Screenshots captured for @{username} at {datetime.datetime.utcnow().isoformat()}Z\nTotal: {len(shots)}\n")
        zf.writestr(f"{username}.json", json.dumps(data, ensure_ascii=False, indent=2))
        for sp in shots:
            try:
                zf.writestr(Path(sp).name, Path(sp).read_bytes())
            except Exception as e:
                logger.warning(f"zip add failed for {sp}: {e}")

    mem.seek(0)
    return StreamingResponse(mem, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{username}_posts.zip"'} )
