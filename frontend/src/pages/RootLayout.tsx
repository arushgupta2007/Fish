import { Toaster } from "@/components/ui/sonner";
import { Outlet } from "react-router";

export default function RootLayout() {
  return <>
    <Outlet />
    <Toaster richColors />
  </>
}
