import { Link, useNavigate } from "react-router-dom";
import { LogOut, User as UserIcon, Building2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-slate-200">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 text-brand-700 font-bold">
          <Building2 className="h-6 w-6" />
          <span className="text-lg">Stayfinder</span>
        </Link>
        <nav className="flex items-center gap-2">
          {user ? (
            <>
              <Link to="/my-bookings">
                <Button variant="ghost" size="sm">My Bookings</Button>
              </Link>
              <Link to="/admin/hotels">
                <Button variant="ghost" size="sm">Admin</Button>
              </Link>
              <div className="ml-2 flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5">
                <UserIcon className="h-4 w-4 text-slate-600" />
                <span className="text-sm text-slate-700">{user.displayName || user.email}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={async () => { await logout(); navigate("/"); }}>
                <LogOut className="h-4 w-4" /> Logout
              </Button>
            </>
          ) : (
            <>
              <Link to="/login"><Button variant="ghost" size="sm">Sign in</Button></Link>
              <Link to="/signup"><Button variant="primary" size="sm">Sign up</Button></Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
