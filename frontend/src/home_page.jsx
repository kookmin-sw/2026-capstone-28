import React, { useState, useRef } from "react";
import { supabase } from "./lib/supabaseClient"; // 프로젝트 내 경로에 맞게 수정
import bgImage from "./assets/profile_background.png";
import { useIsMobile } from "./hooks/useIsMobile";

// ===== Color tokens =====
const C = {
  deep: "#0B3B2E",
  forest: "#13513F",
  emerald: "#2E8B57",
  emeraldLight: "#3CB371",
  mint: "#7FE3B5",
  mintSoft: "#C8F2DC",
  text: "#0E2A20",
  textSoft: "#3B5A4B",
};

const NAV_ITEMS = [
  { key: "home", label: "Home" },
  { key: "analyse", label: "Analyse" },
  { key: "profile", label: "Profile" },
];

export default function HomePage({ onNavigate, onAnalyze }) {
  const [activeNav, setActiveNav] = useState("analyse");
  const [videoA, setVideoA] = useState(null);
  const [videoB, setVideoB] = useState(null);
  const [videoAUrl, setVideoAUrl] = useState("");
  const [videoBUrl, setVideoBUrl] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const isMobile = useIsMobile();

  const handleAnalyze = async () => {
    if ((!videoA && !videoAUrl) || (!videoB && !videoBUrl)) {
      alert("원본 영상과 비교 영상을 모두 업로드하거나 URL로 입력해주세요.");
      return;
    }

    setError(null);
    setIsLoading(true);

    try {

      // Supabase 로그인 토큰 가져오기, 원래거
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        alert("로그인이 필요합니다.");
        setIsLoading(false);
        return;
      } 

      //const session = { access_token: "test-token" };

      const form = new FormData();
      if (videoA) form.append("video_a", videoA);
      if (videoB) form.append("video_b", videoB);


      if (videoAUrl) form.append("video_a_url", videoAUrl);
      if (videoBUrl) form.append("video_b_url", videoBUrl);

      const res = await fetch("https://kpopstand.com/api/videos/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: form,
      });

      const result = await res.json();

      if (!res.ok) {
        // validation.py에서 보내는 에러 메시지 표시
        setError(result.detail);
        return;
      }

      // 성공 → 결과 페이지로 이동
      if (onAnalyze) onAnalyze(result.video_a.vid, result.video_b.vid, result.analysis_id);

    } catch (e) {
      setError("서버 연결에 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.root}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
        rel="stylesheet"
      />

      {/* 배경 레이어 */}
      <div style={styles.bgLayer} />
      <div style={styles.bgTint} />

      {/* ===== Top Navigation ===== */}
      <nav style={styles.navWrap}>
        <div style={styles.navGlow} />
        <div style={styles.nav}>
          <div style={styles.navSheen} />
          {NAV_ITEMS.map((item) => {
            const active = activeNav === item.key;
            return (
              <button
                key={item.key}
                onClick={() => onNavigate && onNavigate(item.key)}
                style={{
                  ...styles.navBtn,
                  ...(isMobile ? { padding: "8px 14px", fontSize: 12 } : {}),
                  ...(active ? styles.navBtnActive : {}),
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* ===== Main Content ===== */}
      <main style={{
        ...styles.main,
        ...(isMobile ? { padding: "85px 4% 40px" } : {}),
      }}>
        <div style={styles.outerCardGlow} />
        <div style={{
          ...styles.outerCard,
          ...(isMobile ? { padding: "28px 18px 32px", borderRadius: 24 } : {}),
        }}>
          <div style={styles.cardSheen} />

          {/* Title */}
          <div style={styles.titleRow}>
            <div style={styles.titleAccent} />
            <h1 style={{
              ...styles.title,
              ...(isMobile ? { fontSize: 24, letterSpacing: -0.5 } : {}),
            }}>
              K-pop <span style={styles.titleGradient}>Visual Studio</span>
            </h1>
          </div>
          <p style={{
            ...styles.subtitle,
            ...(isMobile ? { fontSize: 12, margin: "0 0 24px 12px" } : {}),
          }}>
            두 영상을 업로드하고 AI 기반 안무 유사도 분석을 시작해보세요.
          </p>

          {/* Upload zones */}
          <div style={{
            ...styles.uploadGrid,
            ...(isMobile ? { gridTemplateColumns: "1fr", gap: 16 } : {}),
          }}>
            <UploadZone
              label="원본 영상"
              file={videoA}
              url={videoAUrl}
              onFile={(file) => {
                setVideoA(file);
                setVideoAUrl("");
              }}
              onUrl={(url) => {
                setVideoAUrl(url);
                setVideoA(null);
              }}
              isMobile={isMobile}    // ⭐ 추가
            />
            <UploadZone
              label="비교 영상"
              file={videoB}
              url={videoBUrl}
              onFile={(file) => {
                setVideoB(file);
                setVideoBUrl("");
              }}
              onUrl={(url) => {
                setVideoBUrl(url);
                setVideoB(null);
              }}
              isMobile = {isMobile}
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div style={styles.errorBox}>
              {error.split("\n").map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          )}

          {/* Analyze button */}
          <div style={styles.analyzeWrap}>
            <button
              onClick={handleAnalyze}
              style={{
                ...styles.analyzeBtn,
                ...(isMobile ? { padding: "14px 40px", fontSize: 14, width: "100%" } : {}),
                ...(isLoading ? styles.analyzeBtnDisabled : {}),
              }}
              disabled={isLoading}
            >
              <span style={{ marginRight: 10, fontSize: 16 }}>✦</span>
              {isLoading ? "업로드 중..." : "분석하기"}
            </button>
          </div>

          {/* Feature cards */}
          <div style={{
            ...styles.featureGrid,
            ...(isMobile ? { gridTemplateColumns: "1fr", gap: 12 } : {}),
          }}>
            {[
              ["⚡", "실시간 분석", "AI 기반 고급 알고리즘으로 즉시 유사도 분석"],
              ["🎯", "구간별 탐지", "영상의 각 구간별로 정확한 유사도 점수 제공"],
              ["📊", "상세 보고서", "분석 결과를 시각화된 보고서로 확인"],
            ].map(([icon, title, desc]) => (
              <div key={title} style={{
                ...styles.featureCard,
                ...(isMobile ? {
                  display: "flex", alignItems: "center", gap: 14,
                  textAlign: "left", padding: "16px 18px",
                } : {}),
              }}>
                <div style={{
                  ...styles.featureIcon,
                  ...(isMobile ? { marginBottom: 0, fontSize: 24, flexShrink: 0 } : {}),
                }}>{icon}</div>
                <div>
                  <div style={styles.featureTitle}>{title}</div>
                  <div style={{
                    ...styles.featureDesc,
                    ...(isMobile ? { fontSize: 12 } : {}),
                  }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

/* ---------- Upload Zone ---------- */
const UploadZone = ({ label, file, url, onFile, onUrl, isMobile }) => {
  const ref = useRef();
  const [dragOver, setDragOver] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [tempUrl, setTempUrl] = useState("");
  const isAllowedVideoFile = (f) => {
    if (!f) return false;

    const allowedTypes = ["video/mp4", "video/quicktime"];
    const allowedExts = [".mp4", ".mov"];

    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));

    return allowedTypes.includes(f.type) || allowedExts.includes(ext);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && isAllowedVideoFile(f)) {
      onFile(f);
      setShowMenu(false);
      setShowUrlInput(false);
    } else {
      alert("MP4 또는 MOV 형식의 파일만 업로드할 수 있습니다.");
    }
  };

  const handleFileSelect = (e) => {
    const f = e.target.files[0];

    if (f && isAllowedVideoFile(f)) {
      onFile(f);
      setShowMenu(false);
      setShowUrlInput(false);
    } else if (f) {
      alert("MP4 또는 MOV 형식의 파일만 업로드할 수 있습니다.");
    }
  };

  const handleUrlSubmit = () => {
    const trimmedUrl = tempUrl.trim();

    if (!trimmedUrl) {
      alert("URL을 입력해주세요.");
      return;
    }

    if (
      !trimmedUrl.includes("youtube.com") &&
      !trimmedUrl.includes("youtu.be")
    ) {
      alert("유튜브 URL만 입력할 수 있습니다.");
      return;
    }

    onUrl(trimmedUrl);
    setShowMenu(false);
    setShowUrlInput(false);
  };

  return (
    <div style={styles.uploadCard}>
      <div style={styles.uploadSheen} />
      <div style={styles.uploadBadge}>♪ {label}</div>

      <div
        onClick={() => setShowMenu(true)}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          ...styles.dropZone,
          ...(dragOver ? styles.dropZoneActive : {}),
        }}
      >
        <div style={styles.uploadIcon}>↑</div>
        <div style={styles.uploadText}>
          {file
            ? file.name
            : url
            ? url
            : "영상을 드래그하거나 클릭해서 업로드"}
        </div>

        <div style={styles.uploadHint}>
          MP4/MOV 파일 업로드 또는 유튜브 URL 입력
        </div>

        <input
          ref={ref}
          type="file"
          hidden
          accept="video/mp4,video/quicktime,.mp4,.mov"
          onChange={handleFileSelect}
        />
      </div>
      {showMenu && (
        <div style={styles.uploadMenu}>
          <button
            type="button"
            style={styles.uploadMenuBtn}
            onClick={() => {
              ref.current.click();
            }}
          >
            동영상 업로드
          </button>

          <button
            type="button"
            style={styles.uploadMenuBtn}
            onClick={() => {
              setShowUrlInput(true);
              setShowMenu(false);
            }}
          >
            URL 업로드
          </button>
        </div>
      )}

      {showUrlInput && (
        <div style={styles.urlBox}>
          <input
            value={tempUrl}
            onChange={(e) => setTempUrl(e.target.value)}
            placeholder="유튜브 URL을 입력하세요"
            style={styles.urlInput}
          />

          <div style={styles.urlBtnRow}>
            <button
              type="button"
              style={styles.urlSubmitBtn}
              onClick={handleUrlSubmit}
            >
              등록
            </button>

            <button
              type="button"
              style={styles.urlCancelBtn}
              onClick={() => setShowUrlInput(false)}
            >
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/* ---------- Styles ---------- */
const styles = {
  root: {
    position: "relative",
    minHeight: "100vh",
    width: "100%",
    overflow: "hidden",
    fontFamily: "'Rajdhani','Chakra Petch',sans-serif",
    color: C.text,
    boxSizing: "border-box",
  },
  bgLayer: {
    position: "fixed",
    inset: 0,
    zIndex: 0,
    backgroundImage: `url(${bgImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
  },
  bgTint: {
    position: "fixed",
    inset: 0,
    zIndex: 0,
    background:
      "radial-gradient(1200px 600px at 80% 30%, rgba(255,255,255,0.3), transparent 60%), radial-gradient(900px 500px at 20% 80%, rgba(46,139,87,0.06), transparent 60%)",
    pointerEvents: "none",
  },

  /* ----- Navigation ----- */
  navWrap: {
    position: "fixed",
    top: 24,
    left: 0,
    right: 0,
    display: "flex",
    justifyContent: "center",
    zIndex: 10,
  },
  navGlow: {
    position: "absolute",
    inset: -20,
    background: `radial-gradient(circle at 50% 50%, ${C.mint}40, transparent 70%)`,
    filter: "blur(30px)",
  },
  nav: {
    position: "relative",
    display: "flex",
    gap: 4,
    padding: 6,
    borderRadius: 999,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(28px) saturate(180%)",
    WebkitBackdropFilter: "blur(28px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 20px 50px rgba(11,59,46,0.18)",
      "0 6px 20px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.12)",
    ].join(", "),
    overflow: "hidden",
  },
  navSheen: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 1,
    background:
      "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
  },
  navBtn: {
    padding: "12px 32px",
    borderRadius: 999,
    border: "none",
    cursor: "pointer",
    background: "transparent",
    color: C.forest,
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 15,
    fontWeight: 700,
    letterSpacing: 0.5,
    transition: "all 0.3s",
  },
  navBtnActive: {
    color: "#fff",
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 50%,${C.emerald} 100%)`,
    boxShadow: `0 8px 22px rgba(46,139,87,0.4), inset 0 1px 0 rgba(255,255,255,0.3)`,
  },

  /* ----- Main outer card ----- */
  main: {
    position: "relative",
    zIndex: 1,
    padding: "120px 5% 60px",
  },
  outerCardGlow: {
    position: "absolute",
    top: 80,
    left: "5%",
    right: "5%",
    bottom: 30,
    background: `radial-gradient(ellipse at 50% 50%, ${C.mint}30, transparent 70%)`,
    filter: "blur(60px)",
    zIndex: 0,
  },
  outerCard: {
    position: "relative",
    zIndex: 1,
    padding: "50px 60px 56px",
    borderRadius: 36,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 50%, rgba(200,242,220,0.3) 100%)",
    backdropFilter: "blur(36px) saturate(180%)",
    WebkitBackdropFilter: "blur(36px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 30px 80px rgba(11,59,46,0.2)",
      "0 8px 24px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.12)",
    ].join(", "),
    overflow: "hidden",
  },
  cardSheen: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 1,
    background:
      "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
  },

  /* ----- Title ----- */
  titleRow: { display: "flex", alignItems: "center", gap: 14, marginBottom: 8 },
  titleAccent: {
    width: 4,
    height: 36,
    borderRadius: 4,
    background: `linear-gradient(180deg,${C.forest},${C.mint})`,
    boxShadow: `0 0 20px ${C.mint}`,
  },
  title: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 36,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -1,
  },
  titleGradient: {
    background: `linear-gradient(135deg,${C.forest} 0%,${C.emerald} 50%,${C.emeraldLight} 100%)`,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  subtitle: {
    color: C.textSoft,
    fontSize: 14,
    margin: "0 0 36px 18px",
  },

  /* ----- Upload grid ----- */
  uploadGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 28,
  },
  uploadCard: {
    position: "relative",
    padding: "26px 26px 28px",
    borderRadius: 22,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(24px) saturate(170%)",
    WebkitBackdropFilter: "blur(24px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.85)",
    boxShadow: [
      "0 14px 40px rgba(11,59,46,0.12)",
      "inset 0 1px 0 rgba(255,255,255,0.9)",
      "inset 0 -1px 0 rgba(46,139,87,0.1)",
    ].join(", "),
    overflow: "hidden",
  },
  uploadSheen: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 1,
    background:
      "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.95) 50%, transparent 100%)",
  },
  uploadBadge: {
    display: "inline-block",
    padding: "7px 16px",
    borderRadius: 999,
    background:
      "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.8)",
    color: C.forest,
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: 0.5,
    marginBottom: 18,
    boxShadow: "0 2px 8px rgba(46,139,87,0.15)",
  },
  dropZone: {
    border: `2px dashed rgba(46,139,87,0.3)`,
    borderRadius: 16,
    padding: "56px 20px",
    textAlign: "center",
    cursor: "pointer",
    background:
      "linear-gradient(135deg, rgba(255,255,255,0.4), rgba(255,255,255,0.15))",
    transition: "all 0.25s",
  },
  dropZoneActive: {
    border: `2px dashed ${C.emerald}`,
    background:
      "linear-gradient(135deg, rgba(200,242,220,0.6), rgba(127,227,181,0.3))",
    transform: "scale(1.01)",
  },
  uploadIcon: {
    fontSize: 38,
    color: C.emerald,
    fontWeight: 700,
    lineHeight: 1,
  },
  uploadText: {
    color: C.deep,
    fontWeight: 700,
    marginTop: 14,
    fontSize: 14,
  },
  uploadHint: {
    color: C.textSoft,
    fontSize: 11,
    marginTop: 6,
    letterSpacing: 0.3,
  },

  /* ----- Error box ----- */
  errorBox: {
    margin: "28px 0 0",
    padding: "14px 20px",
    borderRadius: 12,
    background: "rgba(255, 80, 80, 0.08)",
    border: "1px solid rgba(255, 80, 80, 0.3)",
    color: "#7B1C1C",
    fontSize: 13,
    lineHeight: 1.9,
    fontWeight: 600,
  },

  /* ----- Analyze button ----- */
  analyzeWrap: {
    display: "flex",
    justifyContent: "center",
    margin: "44px 0 36px",
  },
  analyzeBtn: {
    padding: "16px 56px",
    borderRadius: 999,
    border: "none",
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 40%,${C.emerald} 100%)`,
    color: "#fff",
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 16,
    fontWeight: 700,
    letterSpacing: 0.8,
    cursor: "pointer",
    boxShadow: `0 14px 36px rgba(46,139,87,0.45), inset 0 1px 0 rgba(255,255,255,0.3)`,
    transition: "transform 0.15s",
  },
  analyzeBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
    boxShadow: "none",
  },

  /* ----- Feature cards ----- */
  featureGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 18,
  },
  featureCard: {
    padding: "22px 20px",
    borderRadius: 18,
    textAlign: "center",
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.3) 100%)",
    backdropFilter: "blur(20px) saturate(160%)",
    WebkitBackdropFilter: "blur(20px) saturate(160%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 8px 24px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.9)",
    ].join(", "),
  },
  featureIcon: {
    fontSize: 22,
    marginBottom: 8,
  },
  featureTitle: {
    fontWeight: 700,
    color: C.deep,
    fontSize: 14,
    marginBottom: 4,
    fontFamily: "'Chakra Petch',sans-serif",
  },
  featureDesc: {
    fontSize: 11.5,
    color: C.textSoft,
    lineHeight: 1.5,
  },
  uploadMenu: {
    marginTop: 14,
    display: "flex",
    justifyContent: "center",
    gap: 12,
  },

  uploadMenuBtn: {
    padding: "10px 18px",
    borderRadius: 999,
    border: "1px solid rgba(46,139,87,0.25)",
    background: "rgba(255,255,255,0.75)",
    color: C.forest,
    fontWeight: 700,
    cursor: "pointer",
    fontFamily: "'Rajdhani',sans-serif",
  },

  urlBox: {
    marginTop: 16,
    padding: 14,
    borderRadius: 14,
    background: "rgba(255,255,255,0.55)",
    border: "1px solid rgba(255,255,255,0.8)",
  },

  urlInput: {
    width: "100%",
    boxSizing: "border-box",
    padding: "12px 14px",
    borderRadius: 10,
    border: "1px solid rgba(46,139,87,0.3)",
    outline: "none",
    color: C.deep,
    fontWeight: 600,
  },

  urlBtnRow: {
    display: "flex",
    justifyContent: "flex-end",
    gap: 8,
    marginTop: 10,
  },

  urlSubmitBtn: {
    padding: "8px 16px",
    borderRadius: 999,
    border: "none",
    background: C.forest,
    color: "#fff",
    fontWeight: 700,
    cursor: "pointer",
  },
  urlCancelBtn: {
    padding: "8px 16px",
    borderRadius: 999,
    border: "1px solid rgba(46,139,87,0.25)",
    background: "rgba(255,255,255,0.8)",
    color: C.forest,
    fontWeight: 700,
    cursor: "pointer",
  },
};