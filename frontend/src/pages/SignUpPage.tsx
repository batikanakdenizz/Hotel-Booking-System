import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { createUserWithEmailAndPassword, updateProfile } from "firebase/auth";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Building2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { firebaseAuth } from "@/lib/firebase";

const Schema = z.object({
  displayName: z.string().min(1, "Required").max(80),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "At least 6 characters"),
});
type FormValues = z.infer<typeof Schema>;

export default function SignUpPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(Schema),
  });

  async function onSubmit(v: FormValues) {
    try {
      const cred = await createUserWithEmailAndPassword(firebaseAuth, v.email, v.password);
      if (cred.user) await updateProfile(cred.user, { displayName: v.displayName });
      toast.success("Account created!");
      navigate("/");
    } catch (e: any) {
      toast.error(e?.message?.replace("Firebase: ", "") || "Sign up failed");
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="hidden md:flex relative overflow-hidden bg-gradient-to-br from-brand-800 to-brand-600 p-12 text-white items-end">
        <div>
          <Building2 className="h-12 w-12 mb-6 opacity-90" />
          <h1 className="text-4xl font-bold leading-tight">Join Stayfinder</h1>
          <p className="mt-3 text-brand-100 text-lg">Free to use, 15% off bookings for members.</p>
        </div>
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-accent/30 blur-3xl" />
      </div>
      <div className="flex items-center justify-center p-6 md:p-12">
        <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm space-y-4">
          <h2 className="text-2xl font-bold text-slate-900">Create account</h2>
          <Input label="Display name" autoComplete="name" error={errors.displayName?.message} {...register("displayName")} />
          <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <Input label="Password" type="password" autoComplete="new-password" error={errors.password?.message} {...register("password")} />
          <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>Sign up</Button>
          <p className="text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-brand-600 hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
