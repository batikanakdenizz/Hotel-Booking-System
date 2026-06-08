import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "accent" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variants: Record<Variant, string> = {
  primary:   "bg-brand-600 hover:bg-brand-700 text-white shadow-sm hover:shadow",
  secondary: "bg-slate-900 hover:bg-slate-800 text-white shadow-sm hover:shadow",
  accent:    "bg-accent hover:bg-accent-dark text-white shadow-sm hover:shadow",
  ghost:     "hover:bg-slate-100 text-slate-700",
  danger:    "bg-red-600 hover:bg-red-700 text-white shadow-sm hover:shadow",
  outline:   "border border-slate-300 hover:bg-slate-50 text-slate-900",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-3 text-sm rounded-md",
  md: "h-10 px-4 text-sm rounded-lg",
  lg: "h-12 px-6 text-base rounded-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading = false, className, children, disabled, ...rest }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium",
        "transition-all duration-150 ease-out active:scale-[0.98]",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
        variants[variant],
        sizes[size],
        className,
      )}
      {...rest}
    >
      {loading && <span className="h-3 w-3 rounded-full border-2 border-current border-t-transparent animate-spin" />}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
