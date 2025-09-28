import { Button } from "@/components/ui/button";
import { useParams } from "react-router-dom";
import { MdFileUpload } from "react-icons/md";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { uploadCSV } from "@/api/sessions";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const Upload = () => {
  const { sessionId } = useParams();
  const queryClient = useQueryClient();

  const [files, setFiles] = useState<FileList | null>(null);

  const { mutate, isPending, error } = useMutation({
    mutationFn: async (file: File) => {
      return await uploadCSV(sessionId || "", file);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["metadata", sessionId],
      });
      toast("Successfully uploaded csv");
    },
    onError: () => toast.error(`Something went wrong when uploading csv`),
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const file = files?.[0];
    if (!file) return;
    mutate(file);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="absolute right-4 top-4 cursor-pointer"
        >
          <MdFileUpload />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Provide a CSV file</DialogTitle>
          </DialogHeader>
          <div>
            <Label htmlFor="csv" className="pb-2">
              Your CSV file
            </Label>
            <Input
              required
              id="csv"
              accept=".csv"
              placeholder="Session name"
              type="file"
              onChange={(e) => setFiles(e.target.files)}
            />
            {error ? (
              <h1 className="pt-0.5 pl-1 text-[0.6rem] text-red-400">
                Something went wrong
              </h1>
            ) : null}
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <div className="flex gap-2">
                <Button variant="outline">Cancel</Button>
                <Button
                  disabled={isPending}
                  className="cursor-pointer"
                  type="submit"
                >
                  Upload File
                </Button>
              </div>
            </DialogClose>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default Upload;
