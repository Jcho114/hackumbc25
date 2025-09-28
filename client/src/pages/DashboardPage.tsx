import { readSessionMetadata } from "@/api/sessions";
import Chat from "@/components/Chat";
import Graph from "@/components/Graph";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Upload from "@/components/Upload";

const DashboardPage = () => {
  const { sessionId } = useParams();

  const {
    data: metadata,
    isPending,
    error,
  } = useQuery({
    queryKey: ["metadata", sessionId],
    queryFn: async () => await readSessionMetadata(sessionId || ""),
    refetchInterval: 3000,
    staleTime: 0,
  });

  if (isPending) {
    return (
      <div className="w-screen h-screen flex justify-center items-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-screen h-screen flex justify-center items-center">
        <Alert variant="destructive">
          <AlertTitle>Something went wrong!</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex">
      <Chat />
      <Graph metadata={metadata} />
      <Upload />
    </div>
  );
};

export default DashboardPage;
