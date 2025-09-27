import { useParams } from "react-router-dom";

const DashboardPage = () => {
  const { sessionId } = useParams();

  return <div className="w-screen">Dashboard</div>;
};

export default DashboardPage;
