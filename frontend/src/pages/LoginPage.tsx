import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useState } from "react";
import { Building2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { firebaseAuth, googleProvider } from "@/lib/firebase";

const Schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "At least 6 characters"),
});
type FormValues = z.infer<typeof Schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/";
  const [busyGoogle, setBusyGoogle] = useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(Schema),
  });

  async function onSubmit(values: FormValues) {
    try {
      await signInWithEmailAndPassword(firebaseAuth, values.email, values.password);
      toast.success("Welcome back!");
      navigate(next);
    } catch (e: any) {
      toast.error(e?.message?.replace("Firebase: ", "") || "Sign in failed");
    }
  }

  async function onGoogle() {
    setBusyGoogle(true);
    try {
      await signInWithPopup(firebaseAuth, googleProvider);
      toast.success("Signed in with Google");
      navigate(next);
    } catch (e: any) {
      toast.error(e?.message?.replace("Firebase: ", "") || "Google sign-in failed");
    } finally {
      setBusyGoogle(false);
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      {/* Hero panel */}
      <div className="hidden md:flex relative overflow-hidden bg-gradient-to-br from-brand-800 to-brand-600 p-12 text-white items-end">
        <div>
          <Building2 className="h-12 w-12 mb-6 opacity-90" />
          <h1 className="text-4xl font-bold leading-tight">Find your next stay</h1>
          <p className="mt-3 text-brand-100 text-lg">Modern hotel booking, 15% off for members.</p>
        </div>
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-accent/30 blur-3xl" />
        <div className="absolute top-10 right-10 h-64 w-64 rounded-full bg-brand-400/30 blur-3xl" />
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center p-6 md:p-12">
        <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm space-y-4">
          <h2 className="text-2xl font-bold text-slate-900">Sign in</h2>
          <p className="text-sm text-slate-500">Use your email or continue with Google.</p>

          <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <Input label="Password" type="password" autoComplete="current-password" error={errors.password?.message} {...register("password")} />

          <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>Sign in</Button>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200" />OR<span className="h-px flex-1 bg-slate-200" />
          </div>

          <Button type="button" variant="outline" className="w-full" size="lg" loading={busyGoogle} onClick={onGoogle}>
            Continue with Google
          </Button>

          <p className="text-center text-sm text-slate-500">
            Don't have an account?{" "}
            <Link to="/signup" className="font-medium text-brand-600 hover:underline">Sign up</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
