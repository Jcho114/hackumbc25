from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict, Any
import os
import json
import pandas as pd
import shutil
import csv

from fastmcp import Client
from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_metadata(session_id):
    with open(os.path.join("sessions", session_id, "metadata.json")) as file:
        metadata = json.loads(file.read())
    return metadata


def dump_metadata(metadata, session_id):
    with open(os.path.join("sessions", session_id, "metadata.json"), "w") as file:
        json.dump(metadata, file)


def create_data_node(
    session_id: str, dataframe: pd.DataFrame, metadata: Dict[str, Any]
) -> str:
    new_node_id = str(uuid4())
    metadata["nodes"].append({"node_id": new_node_id, "type": "data"})
    dataframe.to_csv(
        os.path.join("sessions", session_id, f"{new_node_id}.csv"), index=False
    )
    return new_node_id


def create_scalar_node(metadata, scalar) -> str:
    new_node_id = str(uuid4())
    metadata["nodes"].append({"node_id": new_node_id, "type": "scalar"})
    metadata["scalar_map"][new_node_id] = scalar
    return new_node_id


def create_edge(metadata, src_id: str, dst_id: str, operation: str):
    metadata["edges"].append(
        {"src_id": src_id, "dst_id": dst_id, "operation": operation}
    )


@app.post("/session/init")
def init(session_name: str):
    session_id = str(uuid4())
    os.makedirs(f"sessions/{session_id}", exist_ok=True)

    with open(os.path.join("sessions", session_id, "metadata.json"), "w") as f:
        json.dump(
            {"session_name": session_name, "nodes": [], "edges": [], "scalar_map": {}},
            f,
        )

    return {"session_id": session_id}


@app.get("/session/{session_id}/metadata")
def get_metadata(session_id: str):
    file_path = f"sessions/{session_id}/metadata.json"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Metadata file not found")

    with open(os.path.join("sessions", session_id, "metadata.json"), "r") as file:
        try:
            metadata = json.load(file)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error decoding JSON from file")

    return JSONResponse(content=metadata)

@app.get("/session/{session_id}/node_info")
def get_node_info(session_id: str, node_id: str):
    node_file_path = os.path.join("sessions", session_id, f"{node_id}.csv")
    if not os.path.exists(node_file_path):
        raise HTTPException(status_code=404, detail="File not found")
    data = []
    with open(node_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            data.append(row)
    return JSONResponse(data, status_code=200)


@app.post("/session/{session_id}/upload")
def upload(session_id: str, file: UploadFile):
    # todo - do csv check
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="File is not csv")
    # todo - check session id is valid

    node_id = str(uuid4())

    try:
        with open(os.path.join("sessions", session_id, f"{node_id}.csv"), "wb") as f:
            shutil.copyfileobj(file.file, f)

        with open(os.path.join("sessions", session_id, "metadata.json")) as f:
            metadata = json.loads(f.read())
            if "nodes" not in metadata:
                metadata["nodes"] = []
            metadata["nodes"].append({"node_id": node_id, "type": "data"})

        with open(os.path.join("sessions", session_id, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        return {"node_id": node_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload file")


@app.post("/session/{session_id}/export/{node_id}")
def export(session_id: str, node_id: str):
    file_path = os.path.join("sessions", session_id, f"{node_id}.csv")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


# @app.post("/tools/filter/{session_id}/{node_id}/{column}")
# def tools_filter(session_id: str, node_id: str, column):
#     try: # filter
#         dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
#     except Exception:
#         raise HTTPException(status_code=404, detail="File not found")
#     filtered = dataset[column].filter()

#     # create dataframe node (metadata changes)
#     create_node(dataframe=filtered, node_ids=[node_id], session_id=session_id)

#     return JSONResponse(content=filtered.to_dict(), status_code=200)


@app.post("/tools/sum")
def tools_sum(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    summation = float(dataset[column].sum())

    metadata = load_metadata(session_id)
    dst_node_id = create_scalar_node(metadata, summation)
    create_edge(metadata, node_id, dst_node_id, "sum")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=summation, status_code=200)


@app.post("/tools/mean")
def tools_mean(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    mean = float(dataset[column].mean())

    metadata = load_metadata(session_id)
    dst_node_id = create_scalar_node(metadata, mean)
    create_edge(metadata, node_id, dst_node_id, "mean")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=mean, status_code=200)


@app.post("/tools/min")
def tools_min(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    min = float(dataset[column].min())

    metadata = load_metadata(session_id)
    dst_node_id = create_scalar_node(metadata, min)
    create_edge(metadata, node_id, dst_node_id, "min")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=min, status_code=200)


@app.post("/tools/max")
def tools_max(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    max = float(dataset[column].max())

    metadata = load_metadata(session_id)
    dst_node_id = create_scalar_node(metadata, max)
    create_edge(metadata, node_id, dst_node_id, "max")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=max, status_code=200)


@app.post("/tools/describe")
def tools_describe(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    description = dataset[column].describe()

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(session_id, description, metadata)
    create_edge(metadata, node_id, dst_node_id, "description")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=description.to_dict(), status_code=200)


mcp_client = Client("http://localhost:9000/mcp")
gemini_client = genai.Client()

@app.post("/gemini")
async def call_gemini(session_id: str, prompt: str, sample_rows: int = 5):
    # Load session metadata
    metadata = load_metadata(session_id)

    node_summaries = []

    for node in metadata.get("nodes", []):
        node_id = node["node_id"]
        node_type = node["type"]

        if node_type == "data":
            filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath, nrows=sample_rows)
                    node_summaries.append({
                        "node_id": node_id,
                        "columns": df.columns.tolist(),
                        "sample_data": df.head(sample_rows).to_dict(orient="list"),
                        "num_rows": len(df)
                    })
                except Exception:
                    node_summaries.append({
                        "node_id": node_id,
                        "error": "Could not read CSV"
                    })
        elif node_type == "scalar":
            scalar_value = metadata.get("scalar_map", {}).get(node_id, None)
            node_summaries.append({
                "node_id": node_id,
                "scalar_value": scalar_value
            })

    prompt_text = (
        f"Session ID: {session_id}\n"
        f"Node summaries: {node_summaries}\n"
        f"Instruction: {prompt}"
    )

    async with mcp_client:
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt_text,
            config=genai.types.GenerateContentConfig(
                temperature=0,
                tools=[mcp_client.session],
            ),
        )

    text_output = response.text
    return JSONResponse(content={"response": text_output}, status_code=200)