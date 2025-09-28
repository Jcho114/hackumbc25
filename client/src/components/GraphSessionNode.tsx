import { callSumDataTool, exportCSV } from "@/api/sessions";
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
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { NodeProps } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { saveAs } from "file-saver";
import NodeInfo from "@/components/NodeInfo";

const GraphSessionNode = (props: NodeProps) => {
  const { sessionId } = useParams();
  const queryClient = useQueryClient();

  const {
    mutate: callSumTool,
    isPendingSum,
    error,
  } = useMutation({
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

  const {
    mutate: callExportTool,
    isPendingExport,
    error: exportError,
  } = useMutation({
    mutationFn: async () => {
      const file = await exportCSV(sessionId || "", props.id);
      saveAs(file, `${props.id}.csv`);
    },
    onError: async () => {
      toast.error("Failed to export csv");
    },
  });

  const handleSum = (column: string) => {
    callSumTool(column);
  };

  const handleExport = () => {
    callExportTool();
  };

  return (
    <ContextMenu>
      <ContextMenuTrigger
        className={cn(
          "border-solid flex px-4 py-4 w-[170px] h-[40px] items-center justify-center rounded-md border border-black"
        )}
      >
        <Dialog>
          <DialogTrigger className="w-[160px] h-[40px] flex items-center justify-center">
            <h1 className="truncate text-center text-xs">{props.data.label}</h1>
          </DialogTrigger>
          <DialogContent className="min-w-[50vw]">
            <NodeInfo nodeId={props.id} />
          </DialogContent>
        </Dialog>
        <Handle type="source" position="right" />
        <Handle type="target" position="left" />
      </ContextMenuTrigger>
      <ContextMenuContent className="w-40">
        {props.data.columns && props.data.columns.length > 0 ? (
          <ContextMenuSub>
            <ContextMenuSubTrigger inset>Sum</ContextMenuSubTrigger>
            <ContextMenuSubContent className="overflow-y-auto h-[30vh]">
              {props.data.columns.map((column: string) => (
                <ContextMenuItem onClick={() => handleSum(column)}>
                  {column}
                </ContextMenuItem>
              ))}
            </ContextMenuSubContent>
          </ContextMenuSub>
        ) : null}
        {props.data.columns && props.data.columns.length > 0 ? (
          <ContextMenuSub>
            <ContextMenuSubTrigger inset>Mean</ContextMenuSubTrigger>
            <ContextMenuSubContent className="overflow-y-auto h-[30vh]">
              {props.data.columns.map((column: string) => (
                <ContextMenuItem onClick={() => handleSum(column)}>
                  {column}
                </ContextMenuItem>
              ))}
            </ContextMenuSubContent>
          </ContextMenuSub>
        ) : null}
        {props.data.columns && props.data.columns.length > 0 ? (
          <ContextMenuSub>
            <ContextMenuSubTrigger inset>Min</ContextMenuSubTrigger>
            <ContextMenuSubContent className="overflow-y-auto h-[30vh]">
              {props.data.columns.map((column: string) => (
                <ContextMenuItem onClick={() => handleSum(column)}>
                  {column}
                </ContextMenuItem>
              ))}
            </ContextMenuSubContent>
          </ContextMenuSub>
        ) : null}
        {props.data.columns && props.data.columns.length > 0 ? (
          <ContextMenuSub>
            <ContextMenuSubTrigger inset>Max</ContextMenuSubTrigger>
            <ContextMenuSubContent className="overflow-y-auto h-[30vh]">
              {props.data.columns.map((column: string) => (
                <ContextMenuItem onClick={() => handleSum(column)}>
                  {column}
                </ContextMenuItem>
              ))}
            </ContextMenuSubContent>
          </ContextMenuSub>
        ) : null}
        <ContextMenuSub>
          <ContextMenuSubTrigger inset>More Tools</ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-40">
            <ContextMenuItem onClick={handleExport}>Export</ContextMenuItem>
            <ContextMenuSeparator />
            <ContextMenuItem variant="destructive" disabled>
              Delete
            </ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>
      </ContextMenuContent>
    </ContextMenu>
  );
};

export default GraphSessionNode;
