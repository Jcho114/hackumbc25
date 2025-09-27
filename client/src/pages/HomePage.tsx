import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { IoIosAdd } from "react-icons/io";
import { useLocalStorage } from "usehooks-ts";
import { Card } from "@/components/ui/card";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { createSession } from "@/api/sessions";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, type FormEvent } from "react";

const SESSIONS_KEY = "sessions";

interface SessionKV {
  name: string;
  id: string;
  accessed: Date;
}

const HomePage = () => {
  const [sessions, setSessions, removeSessions] = useLocalStorage(
    SESSIONS_KEY,
    [] as SessionKV[]
  );

  const [sessionName, setSessionName] = useState("");

  const navigate = useNavigate();

  // TODO - Sort by most recently accessed later
  const { mutate, isPending, error } = useMutation({
    mutationFn: async (sessionName: string) => {
      const result = await createSession(sessionName);
      setSessions([
        ...sessions,
        {
          name: sessionName,
          id: result.sessionId,
          accessed: new Date(),
        },
      ]);
      navigate(`/dashboard/${result.sessionId}`);
    },
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    mutate(sessionName);
  };

  return (
    <div className="w-screen min-h-screen flex items-center flex-col gap-6 pt-20 pb-20">
      <h1 className="text-2xl font-bold">Your Sessions</h1>
      <div className="w-full flex flex-col px-14 gap-3">
        <div className="w-full grid grid-cols-3 gap-3">
          <Dialog>
            <DialogTrigger asChild>
              <Card className="w-full h-full flex justify-center items-center py-20 gap-2 bg-gray-50 cursor-pointer">
                <div className="w-10 h-10 flex justify-center items-center">
                  <IoIosAdd className="w-7 h-7" />
                </div>
                <h1 className="text-l font-bold">Create A Session</h1>
              </Card>
            </DialogTrigger>
            <DialogContent>
              <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>Provide a session name</DialogTitle>
                </DialogHeader>
                <div>
                  <Label htmlFor="session" className="pb-2">
                    Your session name
                  </Label>
                  <Input
                    required
                    id="session"
                    placeholder="Session name"
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                  />
                  {error ? (
                    <h1 className="pt-0.5 pl-1 text-[0.6rem] text-red-400">
                      Something went wrong
                    </h1>
                  ) : null}
                </div>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="outline">Cancel</Button>
                  </DialogClose>
                  <Button
                    disabled={isPending}
                    className="cursor-pointer"
                    type="submit"
                  >
                    Create Session
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          {sessions.map((session) => (
            <Link to={`/dashboard/${session.id}`}>
              <Card className="w-full h-full flex justify-center items-center py-20 gap-2 cursor-pointer">
                <Avatar className="w-10 h-10">
                  <AvatarFallback>
                    {session.name.slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <h1 className="text-l font-bold">{session.name}</h1>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
