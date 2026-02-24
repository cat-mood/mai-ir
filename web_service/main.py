#!/usr/bin/env python3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import subprocess
import os

app = FastAPI(title="Boolean Search Engine")

templates = Jinja2Templates(directory="templates")

SEARCH_CLI_PATH = "../search_engine/build/search_cli"
INDEX_DIR = "../search_engine/index"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    if not os.path.exists(SEARCH_CLI_PATH):
        return templates.TemplateResponse("results.html", {
            "request": request,
            "query": query,
            "error": "Search engine not built. Run 'cd search_engine && mkdir build && cd build && cmake .. && make'",
            "results": []
        })
    
    try:
        process = subprocess.Popen(
            [SEARCH_CLI_PATH, INDEX_DIR],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=query + "\n", timeout=30)
        
        results = []
        lines = stdout.strip().split('\n')
        
        parsing_results = False
        for line in lines:
            if line.startswith("Found"):
                parsing_results = True
                continue
            
            if parsing_results and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    doc_id = parts[0].strip()
                    url = parts[1].strip()
                    title = parts[2].strip()
                    results.append({
                        'doc_id': doc_id,
                        'url': url,
                        'title': title
                    })
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "query": query,
            "results": results,
            "total": len(results)
        })
        
    except subprocess.TimeoutExpired:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "query": query,
            "error": "Search timed out",
            "results": []
        })
    except Exception as e:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "query": query,
            "error": f"Error: {str(e)}",
            "results": []
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
