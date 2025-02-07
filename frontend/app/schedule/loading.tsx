import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="container mx-auto py-8 flex flex-col items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-muted-foreground mt-4">Loading your trip schedule...</p>
    </div>
  );
}
