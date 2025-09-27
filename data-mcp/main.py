from fastmcp import FastMCP
import requests

mcp = FastMCP("My MCP Server")

BASE_URL = "http://127.0.0.1:8000/"

@mcp.tool
def greet(name: str) -> str:
    print("yote")
    return f"Fuck you {name}"

@mcp.tool
def mean(session_id: str, node_id: str, column: str):
    """Returns the mean of the given column in the data contained in the given node_id, in the session given by session_id."""
    url = f"{BASE_URL}/tools/mean/{session_id}/{node_id}/{column}"
    resp = requests.post(url)
    resp.raise_for_status()
    return resp.json()

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
    url = f"{BASE_URL}/session/node_info"
    params = {"session_id": session_id, "node_id": node_id}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def main():
    mcp.run(transport="http", host="127.0.0.1", port=9000)

if __name__ == "__main__":
    main()