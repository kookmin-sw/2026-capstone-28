import React, { useState, useEffect } from "react";
import { supabase } from "./lib/supabaseClient";
import Login from "./Login";
import HomePage from "./home_page";
import AboutUsPage from "./about_us_page";
import ProfilePage from "./profile_page";
import ResultPage from "./result_page";
import LoadingPage from "./loading_page";
import { useIsMobile } from "./hooks/useIsMobile";

const BACKEND_URL = "http://localhost:8000";

export default function App() {
  const [page, setPage] = useState("about");
  const [session, setSession] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const isMobile = useIsMobile();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (!session) setPage("about");
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  const navigate = (target) => {
    if (target === "home") {
      setPage("about");
      return;
    }
    if (!session && target !== "about" && target !== "login") {
      setPage("login");
      return;
    }
    setPage(target);
  };

  const handleLogin = () => setPage("analyse");

  const handleAnalyze = async (videoAId, videoBId, analysisId) => {
    setAnalysisError(null);
    setPage("loading");

    try {
      const response = await fetch(`${BACKEND_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_a_id: videoAId,
          video_b_id: videoBId,
          analysis_id: analysisId,
        }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `서버 오류 (${response.status})`);
      }

      const result = await response.json();
      setAnalysisResult(result);
      setPage("result");
    } catch (err) {
      console.error("분석 실패:", err);
      setAnalysisError(err.message);
      setPage("analyse");
      alert(`분석 중 오류가 발생했습니다.\n${err.message}`);
    }
  };

  const logoutBtn = session && page !== "login" && (
    <button onClick={handleLogout} style={{
      ...logoutBtnStyle,
      ...(isMobile ? { padding: "6px 14px", fontSize: 11, top: 14, left: 14 } : {}),
    }}>
      로그아웃
    </button>
  );

  switch (page) {
    case "login":
      return <Login onLogin={handleLogin} />;
    case "about":
      return (
        <>
          {logoutBtn}
          <AboutUsPage onNavigate={navigate} isLoggedIn={!!session} />
        </>
      );
    case "analyse":
      return (
        <>
          {logoutBtn}
          <HomePage onNavigate={navigate} onAnalyze={handleAnalyze} />
        </>
      );
    case "loading":
      return <LoadingPage />;
    case "profile":
      return (
        <>
          {logoutBtn}
          <ProfilePage onNavigate={navigate} />
        </>
      );
    case "result":
      return (
        <>
          {logoutBtn}
          <ResultPage onNavigate={navigate} result={analysisResult} />
        </>
      );
    default:
      return (
        <>
          {logoutBtn}
          <AboutUsPage onNavigate={navigate} isLoggedIn={!!session} />
        </>
      );
  }
}

const logoutBtnStyle = {
  position: "fixed",
  top: 28,
  left: 28,
  zIndex: 20,
  padding: "10px 22px",
  borderRadius: 999,
  border: "1px solid rgba(255,255,255,0.8)",
  background: "linear-gradient(135deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4))",
  backdropFilter: "blur(20px) saturate(160%)",
  WebkitBackdropFilter: "blur(20px) saturate(160%)",
  color: "#0B3B2E",
  fontSize: 13,
  fontWeight: 700,
  fontFamily: "'Rajdhani',sans-serif",
  cursor: "pointer",
  boxShadow: "0 4px 16px rgba(11,59,46,0.12), inset 0 1px 0 rgba(255,255,255,0.9)",
  letterSpacing: 0.3,
};