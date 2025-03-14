import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="container mx-auto pt-[100px] flex flex-col items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm text-muted-foreground mt-4">Loading your trip information...</p>
    </div>
  );
}
