import { Navigate } from "react-router"
import { useAuth } from "../context/AuthContext"

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) return null

  if (!user || !user.isActive || user.role !== "admin") {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
