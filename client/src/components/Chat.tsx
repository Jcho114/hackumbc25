import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

const Chat = () => {
  return (
    <Card className="absolute w-1/4 h-[95%] m-4 z-10 p-4 flex flex-col justify-between">
      <div className="w-fit">
        <h1 className="text-l font-bold text-center">CHAT</h1>
      </div>
      <div className="w-full h-[5rem]">
        <Textarea
          className="w-full border-gray-200 border-[1.5px] rounded-md h-full p-2 text-sm resize-none"
          placeholder="Ask anything here"
        />
      </div>
    </Card>
  );
};

export default Chat;
