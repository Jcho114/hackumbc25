import { callSumDataTool } from "@/api/sessions";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { cn } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { NodeProps } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";

const GraphSessionNode = (props: NodeProps) => {
  const { sessionId } = useParams();
  const queryClient = useQueryClient();

  const { mutate, isPending, error } = useMutation({
    mutationFn: async (column: string) => {
      await callSumDataTool(sessionId || "", props.id, column);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["metadata", sessionId],
      });
      toast.success("Successfully created Sum");
    },
    onError: async () => {
      toast.error("Failed to create Sum");
    },
  });

  const handleSum = () => {
    mutate("count");
  };

  return (
    <ContextMenu>
      <ContextMenuTrigger
        className={cn(
          "border-solid flex px-4 py-4 w-[140px] h-[40px] items-center justify-center rounded-md border border-black",
          isPending ? "animate-pulse" : ""
        )}
      >
        <h1 className="text-sm truncate w-full text-center">{props.id}</h1>
        <Handle type="source" position="right" />
        <Handle type="target" position="left" />
      </ContextMenuTrigger>
      <ContextMenuContent className="w-40">
        <ContextMenuItem onClick={handleSum} inset>
          Sum
        </ContextMenuItem>
        <ContextMenuItem inset>Mean</ContextMenuItem>
        <ContextMenuItem inset>Min</ContextMenuItem>
        <ContextMenuSub>
          <ContextMenuSubTrigger inset>More Tools</ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-40">
            <ContextMenuItem>Save Page...</ContextMenuItem>
            <ContextMenuItem>Create Shortcut...</ContextMenuItem>
            <ContextMenuItem>Name Window...</ContextMenuItem>
            <ContextMenuSeparator />
            <ContextMenuItem>Developer Tools</ContextMenuItem>
            <ContextMenuSeparator />
            <ContextMenuItem variant="destructive">Delete</ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>
      </ContextMenuContent>
    </ContextMenu>
  );
};

export default GraphSessionNode;
