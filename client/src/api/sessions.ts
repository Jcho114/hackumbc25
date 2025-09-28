import api from "./base.ts";

interface CreateSessionResult {
  session_id: string;
}

export async function createSession(sessionName: string) {
  const response = await api.post("/session/init", null, {
    params: {
      session_name: sessionName,
    },
  });
  return response.data as CreateSessionResult;
}

export interface SessionNode {
  node_id: string;
  type: "data" | "scalar";
}

export interface SessionEdge {
  src_id: string;
  dst_id: string;
  operation: string;
}

export interface SessionMetadata {
  session_name: string;
  nodes: SessionNode[];
  edges: SessionEdge[];
  scalar_map: {
    [key: string]: number;
  };
}

export async function readSessionMetadata(sessionId: string) {
  const response = await api.get(`/session/${sessionId}/metadata`);
  return response.data as SessionMetadata;
}
