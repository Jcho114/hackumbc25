import { readSessionMetadata } from "@/api/sessions";
import Graph from "@/components/Graph";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

const DashboardPage = () => {
  const { sessionId } = useParams();

  const {
    data: metadata,
    isPending,
    error,
  } = useQuery({
    queryKey: ["metadata", sessionId],
    queryFn: async () => await readSessionMetadata(sessionId || ""),
  });

  if (isPending) {
    return "Loading...";
  }

  if (error) {
    return error.message;
  }

  return (
    <div className="w-screen h-screen">
      <Graph metadata={metadata} />
    </div>
  );
};

export default DashboardPage;
