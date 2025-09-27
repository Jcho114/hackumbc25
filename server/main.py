from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import List

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

def create_node(node_ids: List[str], session_id: str, scalar=None, dataframe=None):
    if scalar is None and dataframe is None:
        raise HTTPException(status_code=500, detail="create_node called incorrectly")
    
    new_node_id = str(uuid4())
    
    try:
        with open(os.path.join(session_id, "metadata.json")) as file:
            metadata = json.loads(file.read())
        
        # add the node
        metadata["nodes"].append(new_node_id)
        
        # scalar map (dataframes stored in files)
        if scalar is not None:
            metadata["scalar_map"][new_node_id] = scalar
        elif dataframe is not None:
            # Create a new CSV file
            dataframe.to_csv(os.path.join(session_id, f"{new_node_id}.csv"), index=False)

        # create edges
        for parent_node_id in node_ids:
            metadata["edges"].append([parent_node_id, new_node_id])

        with open(os.path.join(session_id, "metadata.json"), "w") as file:
            json.dump(metadata, file)
    
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    
    return new_node_id

@app.post("/session/init")
def init(session_name: str):
    # create session directory
    session_id = str(uuid4())
    os.mkdir(session_id)

    # create metadata file (include name in file)
    with open(os.path.join(session_id, "metadata.json"), "w") as f:
        json.dump({
            "session_name": session_name,
            "nodes": [],
            "edges": [],
            "scalar_map": {}
        }, f)

    # return session id
    return {session_id: session_id}

@app.get("/session/{session_id}/metadata")
def get_metadata(session_id: str):
    file_path = f"{session_id}/metadata.json"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Metadata file not found")

    with open(os.path.join(session_id, "metadata.json"), "r") as file:
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

    # make node id
    node_id = str(uuid4())

    try:
        with open(os.path.join(session_id, f"{node_id}.csv"), "wb") as f:
            shutil.copyfileobj(file.file, f)

        with open(os.path.join(session_id, "metadata.json")) as f:
            metadata = json.loads(f.read())
            if "nodes" not in metadata:
                metadata["nodes"] = []
            metadata["nodes"].append(node_id)

        with open(os.path.join(session_id, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        return {"node_id": node_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload file")

@app.post("/session/{session_id}/export/{node_id}")
def export(session_id: str, node_id: str):
    file_path = os.path.join(session_id, f"{node_id}.csv")

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

@app.post("/tools/sum/{session_id}/{node_id}/{column}")
def tools_sum(session_id: str, node_id: str, column: str):
    try:
        # find sum
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    summation = dataset[column].sum()

    # create scalar node (metadata changes)
    create_node(scalar=summation, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=summation, status_code=200)

@app.post("/tools/mean/{session_id}/{node_id}/{column}")
def tools_mean(session_id: str, node_id: str, column: str):
    try:
        # find mean
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    mean = dataset[column].mean()

    # create scalar node (metadata changes)
    create_node(scalar=mean, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=mean, status_code=200)

@app.post("/tools/min/{session_id}/{node_id}/{column}")
def tools_min(session_id: str, node_id: str, column: str):
    try:
        # find min
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    min = dataset[column].min()

    # create scalar node (metadata changes)
    create_node(scalar=min, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=min, status_code=200)

@app.post("/tools/max/{session_id}/{node_id}/{column}")
def tools_max(session_id: str, node_id: str, column: str):
    try:   
        # find max
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    max = dataset[column].max()

    # create scalar node (metadata changes)
    create_node(scalar=max, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=max, status_code=200)

@app.post("/tools/describe/{session_id}/{node_id}/{column}")
def tools_describe(session_id: str, node_id: str, column: str):
    try:
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    description = dataset[column].describe()

    # create dataframe node (metadata changes)
    create_node(dataframe=description, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=description.to_dict(), status_code=200)

@app.post("/tools/value_counts/{session_id}/{node_id}/{column}")
def tools_value_counts(session_id: str, node_id: str, column: str):
    try:
        dataset = pd.read_csv(f"{session_id}/{node_id}.csv")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    value_counts = dataset[column].value_counts()

    # create dataframe node (metadata changes)
    create_node(dataframe=value_counts, node_ids=[node_id], session_id=session_id)

    return JSONResponse(content=value_counts.to_dict(), status_code=200)