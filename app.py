from pathlib import Path
from typing import Any, Dict
import os
import shutil
import subprocess
import tempfile

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from starlette.background import BackgroundTask
from pydantic import BaseModel

from citation_formatter import prepare_publications

BASE_DIR = Path(__file__).resolve().parent
RESUME_ENGLISH_FILE = BASE_DIR / "resume_english.yaml"
RESUME_FILES = {
    "en": RESUME_ENGLISH_FILE,
    "zh": BASE_DIR / "resume_chinese.yaml",
}
LABELS = {
    "en": {
        "resume": "Resume",
        "position": "Target Position",
        "telephone": "Mobile",
        "email": "Email",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "homepage": "Personal Website",
        "education": "Education",
        "publications": "Publications",
        "research_experience": "Research",
        "work_experience": "Work Experience",
        "projects": "Project",
        "competitions": "Competition",
        "awards": "Selected Awards and Honors",
        "skills": "Skills",
        "tech_stack": "Tech Stack",
        "export_pdf": "Export PDF",
        "edit_yaml": "Edit YAML",
        "yaml_editor": "YAML Editor",
        "save_yaml": "Save YAML",
        "open_preview": "Open Preview",
        "saving": "Saving...",
        "generating": "Generating...",
        "saved_preview": "Saved. Preview refreshed.",
        "save_failed": "Save failed: ",
        "resume_preview": "Resume Preview",
    },
    "zh": {
        "resume": "简历",
        "position": "求职方向",
        "telephone": "电话",
        "email": "邮箱",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "homepage": "个人主页",
        "education": "教育背景",
        "publications": "论文发表",
        "research_experience": "科研经历",
        "work_experience": "工作经历",
        "projects": "项目经历",
        "competitions": "竞赛经历",
        "awards": "奖项与荣誉",
        "skills": "技能",
        "tech_stack": "技术栈",
        "export_pdf": "导出 PDF",
        "edit_yaml": "编辑 YAML",
        "yaml_editor": "YAML 编辑器",
        "save_yaml": "保存 YAML",
        "open_preview": "打开预览",
        "saving": "保存中……",
        "generating": "生成中……",
        "saved_preview": "已保存，预览已刷新。",
        "save_failed": "保存失败：",
        "resume_preview": "简历预览",
    },
}

app = FastAPI(title="best-cv", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount(
    "/img",
    StaticFiles(directory=str(BASE_DIR / "img")),
    name="resume-images",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ResumeDataPayload(BaseModel):
    data: Dict[str, Any]


class ResumeRawPayload(BaseModel):
    yaml_text: str


def _get_lang(lang: str) -> str:
    if lang not in RESUME_FILES:
        raise HTTPException(status_code=400, detail="lang must be en or zh")
    return lang


def _get_resume_file(lang: str) -> Path:
    return RESUME_FILES[_get_lang(lang)]


def _read_resume(lang: str = "en") -> Dict[str, Any]:
    resume_file = _get_resume_file(lang)
    if not resume_file.exists():
        raise HTTPException(status_code=404, detail=f"{resume_file.name} not found")
    text = resume_file.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text) or {}
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail=f"{resume_file.name} top level must be a mapping")
    return parsed


def _write_resume(data: Dict[str, Any], lang: str = "en") -> None:
    _get_resume_file(lang).write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/resume")


@app.get("/resume", response_class=HTMLResponse, include_in_schema=False)
def resume_page(
    request: Request, lang: str = "en", editor_context: bool = False
) -> HTMLResponse:
    lang = _get_lang(lang)
    data = _read_resume(lang)
    return templates.TemplateResponse(
        request,
        "resume.html",
        context={
            "basics": data.get("basics", {}),
            "education": data.get("education", []),
            "education_note": data.get("education_note"),
            "publications": prepare_publications(
                data.get("publications", []),
                data.get("citation_style", "ieee"),
            ),
            "research_experience": data.get("research_experience", []),
            "work_experience": data.get(
                "work_experience", data.get("internships", [])
            ),
            "projects": data.get("projects", []),
            "competitions": data.get("competitions", []),
            "awards": data.get("awards", []),
            "skills": data.get("skills", []),
            "lang": lang,
            "labels": LABELS[lang],
            "editor_context": editor_context,
        },
    )


@app.get("/editor", response_class=HTMLResponse, include_in_schema=False)
def editor_page(request: Request, lang: str = "en") -> HTMLResponse:
    lang = _get_lang(lang)
    resume_file = _get_resume_file(lang)
    yaml_text = resume_file.read_text(encoding="utf-8") if resume_file.exists() else ""
    return templates.TemplateResponse(
        request,
        "editor.html",
        context={"yaml_text": yaml_text, "lang": lang, "labels": LABELS[lang]},
    )


@app.get("/api/resume")
def get_resume_data(lang: str = "en") -> Dict[str, Any]:
    return _read_resume(lang)


@app.put("/api/resume")
def put_resume_data(payload: ResumeDataPayload, lang: str = "en") -> Dict[str, str]:
    _write_resume(payload.data, lang)
    return {"message": f"Updated {_get_resume_file(lang).name}"}


@app.get("/api/resume/raw")
def get_resume_raw(lang: str = "en") -> Dict[str, str]:
    resume_file = _get_resume_file(lang)
    if not resume_file.exists():
        raise HTTPException(status_code=404, detail=f"{resume_file.name} not found")
    return {"yaml_text": resume_file.read_text(encoding="utf-8")}


@app.put("/api/resume/raw")
def put_resume_raw(payload: ResumeRawPayload, lang: str = "en") -> Dict[str, str]:
    try:
        parsed = yaml.safe_load(payload.yaml_text) or {}
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"YAML parse error: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="YAML top level must be a mapping")
    resume_file = _get_resume_file(lang)
    resume_file.write_text(payload.yaml_text, encoding="utf-8")
    return {"message": f"{resume_file.name} saved"}


def _find_browser() -> Path:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise HTTPException(status_code=500, detail="Microsoft Edge or Chrome not found")


def _cleanup_export(pdf_path: str, profile_dir: str) -> None:
    Path(pdf_path).unlink(missing_ok=True)
    shutil.rmtree(profile_dir, ignore_errors=True)


@app.get("/export-pdf")
def export_pdf(request: Request, lang: str = "en") -> FileResponse:
    lang = _get_lang(lang)
    browser = _find_browser()
    url = str(request.base_url).rstrip("/") + f"/resume?lang={lang}"
    fd, out_path = tempfile.mkstemp(suffix=".pdf", prefix="bestresume_")
    os.close(fd)
    profile_dir = tempfile.mkdtemp(prefix="bestresume_browser_")
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile_dir}",
        f"--print-to-pdf={out_path}",
        "--virtual-time-budget=3000",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        pdf_file = Path(out_path)
        if result.returncode != 0 or not pdf_file.exists() or pdf_file.stat().st_size == 0:
            detail = result.stderr.decode(errors="replace")[:300] or "PDF generation failed"
            _cleanup_export(out_path, profile_dir)
            raise HTTPException(status_code=500, detail=detail)
        return FileResponse(
            out_path,
            filename="Resume_Chinese.pdf" if lang == "zh" else "Resume_English.pdf",
            media_type="application/pdf",
            background=BackgroundTask(_cleanup_export, out_path, profile_dir),
        )
    except subprocess.TimeoutExpired as exc:
        _cleanup_export(out_path, profile_dir)
        raise HTTPException(status_code=500, detail="PDF generation timed out") from exc


if __name__ == "__main__":
    import sys
    import platform
    import threading

    host = "127.0.0.1"
    port = 8020

    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    if platform.system() == "Windows":
        url = f"http://{host}:{port}"
        threading.Timer(1.5, lambda: __import__("os").startfile(url)).start()

    uvicorn.run("app:app", host=host, port=port, reload=True)
