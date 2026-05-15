import React, { useState, useEffect } from "react";
import { useIsMobile } from "./hooks/useIsMobile";

const C = {
  deep: "#0B3B2E",
  forest: "#13513F",
  emerald: "#2E8B57",
  mint: "#7FE3B5",
  text: "#0E2A20",
  textSoft: "#3B5A4B",
};

const STAGES = [
  "영상을 분석하고 있어요",
  "안무 동작을 추출하는 중",
  "춤추는 모든 사람을 응원합니다",
  "딥러닝 모델이 비교 중",
  "Tenein은 라틴어로 무용입니다",
  "유사 구간을 찾고 있어요",
  "춤은 인류의 가장 오래된 언어 중 하나입니다",
  "한 동작에 담긴 수백 번의 반복을 기억합니다",
  "분석 보고서를 작성 중",
];

export default function LoadingPage() {
  const [stageIdx, setStageIdx] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const isMobile = useIsMobile();

  // 단계별 메시지 자동 전환 (매 12초)
  useEffect(() => {
    const interval = setInterval(() => {
      setStageIdx((prev) => (prev + 1) % STAGES.length);
    }, 12000);
    return () => clearInterval(interval);
  }, []);

  // 경과 시간 카운터
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.root}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;700&family=Rajdhani:wght@500;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse {
          0%, 100% { opacity: 0.4; transform: scale(0.95); }
          50%      { opacity: 1;   transform: scale(1.05); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div style={styles.bgTint} />

      <div style={styles.center}>
        {/* 회전 링 */}
        <div style={{
          ...styles.spinnerWrap,
          ...(isMobile ? { width: 100, height: 100, margin: "0 auto 28px" } : {}),
        }}>
          <div style={styles.spinnerOuter} />
          <div style={styles.spinnerInner} />
          <div style={styles.spinnerCore} />
        </div>

        {/* 메시지 (key로 fadeIn 재생성) */}
        <h2 style={{
          ...styles.title,
          ...(isMobile ? { fontSize: 20, padding: "0 20px" } : {}),
        }} key={stageIdx}>
          {STAGES[stageIdx]}
        </h2>

        <p style={styles.subtitle}>
          분석에는 약 5분 정도 소요됩니다
        </p>

        <div style={styles.elapsed}>
          {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
        </div>
      </div>
    </div>
  );
}

const styles = {
  root: {
    position: "relative",
    minHeight: "100vh",
    width: "100%",
    overflow: "hidden",
    fontFamily: "'Rajdhani','Chakra Petch',sans-serif",
    background: "#F2EEE3",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  bgTint: {
    position: "fixed",
    inset: 0,
    background: `radial-gradient(ellipse at 50% 50%, ${C.mint}30, transparent 70%)`,
    pointerEvents: "none",
  },
  center: {
    position: "relative",
    textAlign: "center",
    zIndex: 1,
  },
  spinnerWrap: {
    position: "relative",
    width: 140,
    height: 140,
    margin: "0 auto 40px",
  },
  spinnerOuter: {
    position: "absolute",
    inset: 0,
    border: `3px solid ${C.mint}40`,
    borderTopColor: C.emerald,
    borderRadius: "50%",
    animation: "spin 1.8s linear infinite",
  },
  spinnerInner: {
    position: "absolute",
    inset: 18,
    border: `3px solid ${C.mint}60`,
    borderRightColor: C.forest,
    borderRadius: "50%",
    animation: "spin 2.4s linear infinite reverse",
  },
  spinnerCore: {
    position: "absolute",
    inset: 45,
    background: `radial-gradient(circle, ${C.mint}, ${C.emerald})`,
    borderRadius: "50%",
    animation: "pulse 1.5s ease-in-out infinite",
    boxShadow: `0 0 30px ${C.mint}`,
  },
  title: {
    fontFamily: "'Chakra Petch', sans-serif",
    fontSize: 28,
    fontWeight: 700,
    color: C.deep,
    margin: "0 0 12px",
    letterSpacing: -0.5,
    animation: "fadeIn 0.5s ease-out",
  },
  subtitle: {
    fontSize: 15,
    color: C.textSoft,
    margin: "0 0 32px",
    fontWeight: 500,
  },
  elapsed: {
    display: "inline-block",
    padding: "8px 24px",
    borderRadius: 999,
    background: "rgba(255,255,255,0.7)",
    border: `1px solid ${C.mint}`,
    color: C.emerald,
    fontFamily: "'Chakra Petch', monospace",
    fontSize: 16,
    fontWeight: 700,
    boxShadow: `0 4px 20px ${C.mint}40`,
  },
};