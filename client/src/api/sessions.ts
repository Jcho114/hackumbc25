import api from "./base.ts";

interface CreateSessionResult {
  sessionId: string;
}

export async function createSession(sessionName: string) {
  const response = await api.post("/session/init", null, {
    params: {
      session_name: sessionName,
    },
  });
  return response.data as CreateSessionResult;
}
