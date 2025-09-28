from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict, Any
import os
import json
import pandas as pd
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
FILTER_OPERATORS = {
    'lt': lambda x, value: x < value,
    'gt': lambda x, value: x > value,
    'eq': lambda x, value: x == value,
    'ne': lambda x, value: x != value,
    'le': lambda x, value: x <= value,
    'ge': lambda x, value: x >= value,
}

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

@app.post("/tools/filter/")
def tools_filter(session_id: str, node_id: str, column, filter_operator: str, filter_value: float):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    if filter_operator not in FILTER_OPERATORS:
        raise HTTPException(status_code=400, detail="Invalid operator")
    # trust
    filtered = dataset[FILTER_OPERATORS[filter_operator](dataset[column], filter_value)]

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(session_id=session_id, dataframe=filtered, metadata=metadata)
    create_edge(metadata, node_id, dst_node_id, "filter")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=filtered.to_dict(), status_code=200)

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


@app.post("/tools/value_counts")
def tools_value_counts(session_id: str, node_id: str, column: str):
    try:
        filepath = os.path.join("sessions", session_id, f"{node_id}.csv")
        dataset = pd.read_csv(filepath)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    value_counts = dataset[column].value_counts()

    metadata = load_metadata(session_id)
    dst_node_id = create_data_node(session_id, value_counts, metadata)
    create_edge(metadata, node_id, dst_node_id, "description")
    dump_metadata(metadata, session_id)

    return JSONResponse(content=value_counts.to_dict(), status_code=200)
