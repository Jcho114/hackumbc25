import io
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict, Any
import os
import json
import pandas as pd
import csv
from typing import Optional
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
FILTER_OPERATORS = {
    "lt": lambda x, value: x < value,
    "gt": lambda x, value: x > value,
    "eq": lambda x, value: x == value,
    "ne": lambda x, value: x != value,
    "le": lambda x, value: x <= value,
    "ge": lambda x, value: x >= value,
}


def load_metadata(session_id):
    with open(os.path.join("sessions", session_id, "metadata.json")) as file:
        metadata = json.loads(file.read())
    return metadata


def dump_metadata(metadata, session_id):
    with open(os.path.join("sessions", session_id, "metadata.json"), "w") as file:
        json.dump(metadata, file)
        file.flush()
        os.fsync(file.fileno())


def create_data_node(
    session_id: str, dataframe: pd.DataFrame, metadata: Dict[str, Any], node_name: str
) -> str:
    new_node_id = str(uuid4())
    metadata["nodes"].append(
        {
            "node_id": new_node_id,
            "node_name": node_name,
            "type": "data",
            "columns": 1 if isinstance(dataframe, pd.Series) else list(dataframe.columns),
        }
    )
    dataframe.to_csv(
        os.path.join("sessions", session_id, f"{new_node_id}.csv"), index=False
    )
    return new_node_id


def create_scalar_node(metadata, scalar, node_name) -> str:
    new_node_id = str(uuid4())
    metadata["nodes"].append(
        {"node_id": new_node_id, "node_name": node_name, "type": "scalar"}
    )
    metadata["scalar_map"][new_node_id] = scalar
    return new_node_id


def create_edge(metadata, src_id: str, dst_id: str, operation: str):
    metadata["edges"].append(
        {"src_id": src_id, "dst_id": dst_id, "operation": operation}
    )

def delete_node_helper(session_id: str, node_id: str, metadata):
    base_path = f"sessions/{session_id}"
    edges = metadata["edges"]
    node_id_exists = False
    node_id_idx = 0
    for index,node in enumerate(metadata["nodes"]):
        if node["node_id"] == node_id:
            node_id_exists = True
            node_id_idx = index
            break
    if not node_id_exists:
        raise HTTPException(status_code=404, detail=f"{node_id} Node not in metadata")
    
    # Recursively delete "child" nodes and edges
    edges = [edge for edge in edges if edge["src_id"] != node_id or not delete_node_helper(session_id, edge["dst_id"], metadata)]
    
    # delete this node
    del metadata["nodes"][node_id_idx]
    node_file_path = os.path.join(base_path, f"{node_id}.csv") 
    if os.path.exists(node_file_path):
        os.remove(node_file_path)
    else:
        raise HTTPException(status_code=404, detail=f"{node_file_path} Node file doesn't exist")

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
    with open(node_file_path, mode="r", newline="", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            data.append(row)
    return JSONResponse(data, status_code=200)


@app.post("/session/{session_id}/upload")
async def upload(session_id: str, file: UploadFile):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="File is not csv")
    # todo - check session id is valid

    contents = await file.read()
    dataframe = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    node_id = str(uuid4())

    try:
        with open(os.path.join("sessions", session_id, f"{node_id}.csv"), "wb") as f:
            f.write(contents)

        with open(os.path.join("sessions", session_id, "metadata.json")) as f:
            metadata = json.loads(f.read())
            if "nodes" not in metadata:
                metadata["nodes"] = []
            metadata["nodes"].append(
                {
                    "node_id": node_id,
                    "node_name": file.filename,
                    "type": "data",
                    "columns": list(dataframe.columns),
                }
            )

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


@app.post("/tools/filter/")
def tools_filter(
    session_id: str, node_id: str, column, filter_operator: str, filter_value: float
):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(status_code=400, detail="Bad request (cannot sum scalar)")
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    if filter_operator not in FILTER_OPERATORS:
        raise HTTPException(status_code=400, detail="Invalid operator")
    # trust
    try:
        filtered = dataset[
            FILTER_OPERATORS[filter_operator](dataset[column], filter_value)
        ]
    except Exception:
        raise HTTPException(status_code=400, detail="Column is not a float")

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(
        session_id=session_id,
        dataframe=filtered,
        metadata=metadata,
        node_name="filter()",
    )
    create_edge(metadata, node_id, dst_node_id, "filter")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=filtered.to_dict(), status_code=200)


@app.post("/tools/sum")
def tools_sum(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(status_code=400, detail="Bad request (cannot sum scalar)")
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    if gb_col is not None:
        gb_sum = pd.DataFrame(dataset.groupby(gb_col)[column].sum())
        dst_node_id = create_data_node(session_id, gb_sum, metadata, "sum()")
        content = gb_sum.to_dict()
    else:
        content = float(dataset[column].sum())
        dst_node_id = create_scalar_node(metadata, content, f"sum({column})")
    create_edge(metadata, node_id, dst_node_id, f"sum({column})")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=content, status_code=200)


@app.post("/tools/mean")
def tools_mean(
    session_id: str, node_id: str, column: str, gb_col: Optional[str] = None
):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(status_code=400, detail="Bad request (cannot mean scalar)")
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    if gb_col is not None:
        gb_mean = pd.DataFrame(dataset.groupby(gb_col)[column].mean())
        dst_node_id = create_data_node(session_id, gb_mean, metadata, "mean()")
        content = gb_mean.to_dict()
    else:
        content = float(dataset[column].mean())
        dst_node_id = create_scalar_node(metadata, content, f"mean({column})")
    create_edge(metadata, node_id, dst_node_id, f"mean({column})")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=content, status_code=200)


@app.post("/tools/min")
def tools_min(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(status_code=400, detail="Bad request (cannot min scalar)")
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    if gb_col is not None:
        gb_min = pd.DataFrame(dataset.groupby(gb_col)[column].min())
        dst_node_id = create_data_node(session_id, gb_min, metadata, "min()")
        content = gb_min.to_dict()
    else:
        content = float(dataset[column].min())
        dst_node_id = create_scalar_node(metadata, content, f"min({column})")
    create_edge(metadata, node_id, dst_node_id, f"min({column})")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=content, status_code=200)


@app.post("/tools/max")
def tools_max(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(status_code=400, detail="Bad request (cannot max scalar)")
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    if gb_col is not None:
        gb_max = pd.DataFrame(dataset.groupby(gb_col)[column].max())
        dst_node_id = create_data_node(session_id, gb_max, metadata, "max()")
        content = gb_max.to_dict()
    else:
        content = float(dataset[column].max())
        dst_node_id = create_scalar_node(metadata, content, f"max({column})")
    create_edge(metadata, node_id, dst_node_id, f"max({column})")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=content, status_code=200)


@app.post("/tools/describe")
def tools_describe(session_id: str, node_id: str, column: str):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(
            status_code=400, detail="Bad request (cannot describe scalar)"
        )
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    description = dataset[column].describe()

    dst_node_id = create_data_node(
        session_id, pd.DataFrame(description), metadata, "describe()"
    )
    create_edge(metadata, node_id, dst_node_id, "description")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=description.to_dict(), status_code=200)


@app.post("/tools/sample")
def tools_sample(session_id: str, node_id: str, n: int):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(
            status_code=400, detail="Bad request (cannot sample scalar)"
        )
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    sample = dataset.sample(n)

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(session_id, sample, metadata, "sample()")

    create_edge(metadata, node_id, dst_node_id, "sample")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=sample.to_dict(), status_code=200)


@app.post("/tools/value_counts")
def tools_value_counts(session_id: str, node_id: str, column: str):
    metadata = load_metadata(session_id)
    node = next(n for n in metadata["nodes"] if n["node_id"] == node_id)
    if node["type"] != "data":
        raise HTTPException(
            status_code=400, detail="Bad request (cannot value count scalar)"
        )
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    value_counts = dataset[column].value_counts()

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(session_id, value_counts, metadata, "value_counts()")
    create_edge(metadata, node_id, dst_node_id, "description")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=value_counts.to_dict(), status_code=200)


mcp_client = Client("http://localhost:9000/mcp")
gemini_client = genai.Client()


@app.post("/gemini")
async def call_gemini(session_id: str, prompt: str, sample_rows: int = 5):
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
                    node_summaries.append(
                        {
                            "node_id": node_id,
                            "columns": df.columns.tolist(),
                            "sample_data": df.head(sample_rows).to_dict(orient="list"),
                            "num_rows": len(df),
                        }
                    )
                except Exception:
                    node_summaries.append(
                        {"node_id": node_id, "error": "Could not read CSV"}
                    )
        elif node_type == "scalar":
            scalar_value = metadata.get("scalar_map", {}).get(node_id, None)
            node_summaries.append({"node_id": node_id, "scalar_value": scalar_value})

    prompt_text = (
        f"Session ID: {session_id}\n"
        f"Node summaries: {node_summaries}\n"
        f"Instruction: {prompt}"
    )

    async def gemini_stream():
        async with mcp_client:
            async for event in await gemini_client.aio.models.generate_content_stream(
                model="gemini-2.0-flash-lite",
                contents=prompt_text,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[mcp_client.session],
                ),
            ):
                if event.candidates:
                    for part in event.candidates[0].content.parts:
                        if part.text:
                            yield f"TEXT::{part.text}"
                        elif getattr(part, "function_call", None):
                            yield f"MCP_CALL::{part.function_call.name}"
                        elif getattr(part, "function_response", None):
                            yield f"MCP_RESULT::{part.function_response}"

    return StreamingResponse(gemini_stream(), media_type="text/plain")

@app.post("/tools/delete_node")
def delete_node(session_id: str, node_id: str):
    try:
        metadata = load_metadata(session_id)
        delete_node_helper(session_id, node_id, metadata)
        dump_metadata(session_id=session_id, metadata=metadata)
        return JSONResponse(content="Node successfully deleted",status_code=200)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")