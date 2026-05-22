import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { AuthProvider } from "@/hooks/useAuth";
import { Header } from "@/components/layout/Header";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ChatWidget } from "@/components/ChatWidget";
import { Spinner } from "@/components/ui/Spinner";

const HomePage = lazy(() => import("@/pages/HomePage"));
const SearchResultsPage = lazy(() => import("@/pages/SearchResultsPage"));
const HotelDetailPage = lazy(() => import("@/pages/HotelDetailPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SignUpPage = lazy(() => import("@/pages/SignUpPage"));
const MyBookingsPage = lazy(() => import("@/pages/MyBookingsPage"));
const AdminHotelsPage = lazy(() => import("@/pages/AdminHotelsPage"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function Loader() {
  return (
    <div className="grid h-[60vh] place-items-center">
      <Spinner />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Auth pages have no header */}
            <Route path="/login" element={<Suspense fallback={<Loader />}><LoginPage /></Suspense>} />
            <Route path="/signup" element={<Suspense fallback={<Loader />}><SignUpPage /></Suspense>} />

            {/* All other pages get the chrome */}
            <Route
              path="/*"
              element={
                <>
                  <Header />
                  <Suspense fallback={<Loader />}>
                    <Routes>
                      <Route path="/" element={<HomePage />} />
                      <Route path="/search" element={<SearchResultsPage />} />
                      <Route path="/hotels/:hotelId" element={<HotelDetailPage />} />
                      <Route
                        path="/my-bookings"
                        element={
                          <ProtectedRoute>
                            <MyBookingsPage />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/admin/hotels"
                        element={
                          <ProtectedRoute>
                            <AdminHotelsPage />
                          </ProtectedRoute>
                        }
                      />
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Suspense>
                  <ChatWidget />
                </>
              }
            />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </QueryClientProvider>
  );
}

function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">Page not found</h1>
      <p className="mt-2 text-slate-500">The page you're looking for doesn't exist.</p>
    </div>
  );
}
