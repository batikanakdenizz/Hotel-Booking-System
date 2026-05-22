import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn("inline-block h-5 w-5 rounded-full border-2 border-brand-500 border-t-transparent animate-spin", className)}
      role="status"
      aria-label="loading"
    />
  );
}
