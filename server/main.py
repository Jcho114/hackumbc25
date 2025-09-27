from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4

import os
import json
import pandas as pd
import shutil

app = FastAPI()


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
    return session_id


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


@app.post("/tools/sum")
def tools_sum(dataset):
    # Sum (Dataset, column, [groupbycolumn]) -> Scalar
    pass


@app.post("/tools/filter")
def tools_filter():
    pass


@app.post("/tools/mean/{session_id}/{node_id},{column}")
def tools_mean(session_id: str, node_id: str, column: str):
    # find mean
    try:
        dataset = pd.read_csv(f"{session_id}/{node_id}")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    mean = dataset[column].mean()

    # create scalar node (metadata changes)
    scalar_node_id = str(uuid4())
    with open(os.path.join(session_id, "metadata.json")) as file:
        metadata = json.loads(file.read())
        metadata["nodes"].append(scalar_node_id)
        metadata["scalar_map"][scalar_node_id] = mean



@app.post("/tools/{session_id}/min")
def tools_min():
    pass


@app.post("/tools/max")
def tools_max():
    pass


@app.post("/tools/describe")
def tools_describe():
    pass
