from fastmcp import FastMCP
import requests
from typing import Optional

mcp = FastMCP("My MCP Server")

BASE_URL = "http://127.0.0.1:8000/"


@mcp.tool
def get_metadata(session_id: str):
    """Returns all of the metadata (information on the session name, node IDs, and edges between nodes)."""
    url = f"{BASE_URL}/session/{session_id}/metadata"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def get_node_info(session_id: str, node_id: str):
    """Returns the contents contained in the given node ID."""
    url = f"{BASE_URL}/session/{session_id}/node_info"
    params = {"session_id": session_id, "node_id": node_id}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_sum(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    """Returns the sum(s) of the given column in the data contained in the given node_id (grouped values by gb_col if given), and creates a corresponding scalar node with an edge from the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/sum"
    params = {
        "session_id": session_id,
        "node_id": node_id,
        "column": column,
        "gb_col": gb_col,
    }
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_mean(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    """Returns the mean of the given column in the data contained in the given node_id (grouped values by gb_col if given), and creates a corresponding scalar node with an edge from the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/mean"
    params = {
        "session_id": session_id,
        "node_id": node_id,
        "column": column,
        "gb_col": gb_col,
    }
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_min(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    """Returns the min of the given column in the data contained in the given node_id (grouped values by gb_col if given), and creates a corresponding scalar node with an edge from the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/min"
    params = {
        "session_id": session_id,
        "node_id": node_id,
        "column": column,
        "gb_col": gb_col,
    }
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_max(session_id: str, node_id: str, column: str, gb_col: Optional[str] = None):
    """Returns the max of the given column in the data contained in the given node_id (grouped values by gb_col if given), and creates a corresponding scalar node with an edge from the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/max"
    params = {
        "session_id": session_id,
        "node_id": node_id,
        "column": column,
        "gb_col": gb_col,
    }
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_describe(session_id: str, node_id: str, column: str):
    """Returns summary statistics on the given column in the data contained in the given node_id, and creates a corresponding data node with an edge from the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/describe"
    params = {"session_id": session_id, "node_id": node_id, "column": column}
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_sample(session_id: str, node_id: str, n: int):
    """Returns a random sample of n rows of the data contained in the given node_id, and creates a corresponding data node with an edge coming from the given node_id, in the given session_id."""
    url = f"{BASE_URL}/tools/sample"
    params = {"session_id": session_id, "node_id": node_id, "n": n}
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool
def make_value_counts(session_id: str, node_id: str, column: str):
    """Returns a list of the counts of unique values in the given column in data contained in the given node_id, and creates a corresponding data node with an edge coming from the given node_id, in the given session_id."""
    url = f"{BASE_URL}/tools/value_counts"
    params = {"session_id": session_id, "node_id": node_id, "column": column}
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    return resp.json()


def main():
    mcp.run(transport="http", host="127.0.0.1", port=9000)


if __name__ == "__main__":
    main()
