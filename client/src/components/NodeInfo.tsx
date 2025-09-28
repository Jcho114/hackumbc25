"use client";

import { getNodeContents, type SessionMetadata } from "@/api/sessions";
import LoadingSpinner from "@/components/LoadingSpinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { useMemo } from "react";

interface NodeInfoProps {
  nodeId: string;
}

const NodeInfo = ({ nodeId }: NodeInfoProps) => {
  const { sessionId } = useParams();
  const queryClient = useQueryClient();

  const queryKey = ["metadata", sessionId];
  const metadata = queryClient.getQueryData(queryKey) as SessionMetadata;
  const nodeInfo = metadata.nodes.find((node) => node.node_id === nodeId);

  const { data, isPending, error } = useQuery({
    queryKey: ["nodedata", nodeId],
    queryFn: async () => {
      if (!nodeInfo || nodeInfo.type === "scalar") {
        return { scalar: 10 };
      }
      const data = await getNodeContents(sessionId || "", nodeId);
      return { data: data };
    },
  });

  const columns = useMemo<ColumnDef<any>[]>(
    () =>
      (nodeInfo?.columns || []).map((col) => ({
        accessorKey: col,
        header: col,
        cell: (info) => info.getValue(),
      })),
    [nodeInfo?.columns]
  );

  const table = useReactTable({
    data: data?.data || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  if (isPending) {
    return (
      <div className="w-full h-full flex justify-center items-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex justify-center items-center">
        <Alert variant="destructive">
          <AlertTitle>Something went wrong!</AlertTitle>
          <AlertDescription>{(error as Error).message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (data?.scalar) {
    return (
      <div className="w-full h-full flex flex-col justify-center items-center">
        <h1 className="text-lg font-bold">{nodeInfo?.node_name}</h1>
        <p>{data.scalar}</p>
      </div>
    );
  }

  if (!data?.data) {
    return <p>Data not found</p>;
  }

  return (
    <div className="w-full h-full flex flex-col justify-center">
      <div className="w-full flex flex-col items-center justify-center">
        <h1 className="mb-2 font-bold">{nodeInfo?.node_name}</h1>
        <div className="rounded-md border overflow-x-auto max-w-[45vw]">
          <Table className="w-full">
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id}>
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-between py-4 px-4">
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
        <span className="text-sm text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} of{" "}
          {table.getPageCount()}
        </span>
      </div>
    </div>
  );
};

export default NodeInfo;
