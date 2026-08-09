import { useEffect, useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import MediaLibraryPage from "./pages/MediaLibraryPage";
import SiteContentPage from "./pages/SiteContentPage";
import { getStoredToken } from "./lib/api";

const currentRoute = () => window.location.hash.replace(/^#/, "") || "/login";

export default function App() {
  const [route, setRoute] = useState(currentRoute);

  useEffect(() => {
    const handleHashChange = () => setRoute(currentRoute());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  if (!getStoredToken() && route !== "/login") {
    return <LoginPage />;
  }

  switch (route) {
    case "/dashboard":
      return <DashboardPage />;
    case "/content":
      return <SiteContentPage />;
    case "/media":
      return <MediaLibraryPage />;
    default:
      return <LoginPage />;
  }
}
