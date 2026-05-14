import React, { useState, useRef, useEffect } from "react";
import { useIsMobile } from "./hooks/useIsMobile";
import bgImage from "./assets/profile_background.png";
import { generatePDF } from "./utils/generatePDF";

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

const BODY_PART_LABELS = {
  left_arm:  "왼팔",
  right_arm: "오른팔",
  left_leg:  "왼다리",
  right_leg: "오른다리",
  torso:     "몸통",
};

const formatTime = (range) => {
  if (!range) return "";
  const fmt = (sec) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };
  return `${fmt(range.start)} - ${fmt(range.end)}`;
};

const MOCK_RESULT = {
  video_url_a: null,
  video_url_b: null,
  overall: { score: 78.6, interpretation: "전체 유사도 해석이 여기 표시됩니다." },
  summary: "두 K-pop 뮤직비디오의 안무 패턴을 비교 분석한 결과입니다.",
  key_differences: [
    "안무 동작의 기본 구조가 매우 유사함",
    "음악 비트에 맞춘 타이밍이 일치",
    "신체 각도 및 포지셔닝에 높은 유사성",
  ],
  segments: [
    {
      id: 1, score: 92,
      video_a: { start: 10, end: 15 },
      video_b: { start: 10, end: 15 },
      description: "회전 동작과 팔 움직임이 거의 동일한 구간",
      body_parts: { left_arm: 0.82, right_arm: 0.79, left_leg: 0.91, right_leg: 0.88, torso: 0.95 },
    },
    {
      id: 2, score: 87,
      video_a: { start: 20, end: 25 },
      video_b: { start: 35, end: 40 },
      description: "점프 및 착지 타이밍과 방향이 유사",
      body_parts: { left_arm: 0.70, right_arm: 0.85, left_leg: 0.78, right_leg: 0.82, torso: 0.90 },
    },
  ],
};

export default function ResultPage({ onNavigate, result }) {
  const [activeNav, setActiveNav] = useState("analyse");
  const [openId, setOpenId] = useState(null);
  const isMobile = useIsMobile();

  const [pdfLoading, setPdfLoading] = useState(false);
  const handlePDF = async () => {
    setPdfLoading(true);
    try {
      await generatePDF(data);
    } finally {
      setPdfLoading(false);
    }
  };

  const data = result || MOCK_RESULT;

  return (
    <div style={styles.root}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        @keyframes expandDown {
          from { opacity: 0; transform: translateY(-10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div style={styles.bgLayer} />
      <div style={styles.bgTint} />

      {/* ===== Navigation ===== */}
      <nav style={styles.navWrap}>
        <div style={styles.navGlow} />
        <div style={{
          ...styles.nav,
          ...(isMobile ? { gap: 2, padding: 4 } : {}),
        }}>
          <div style={styles.cardSheen} />
          {NAV_ITEMS.map((item) => {
            const active = activeNav === item.key;
            return (
              <button
                key={item.key}
                onClick={() => {
                  setActiveNav(item.key);
                  if (onNavigate) onNavigate(item.key);
                }}
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
        ...(isMobile ? {
          gridTemplateColumns: "1fr",
          padding: "85px 4% 40px",
          gap: 24,
        } : {}),
      }}>

        {/* ============ LEFT COLUMN ============ */}
        <div style={styles.leftColumn}>

          {/* 전체 유사도 카드 */}
          <section style={styles.cardWrap}>
            <div style={styles.cardGlow} />
            <div style={{
              ...styles.scoreCard,
              ...(isMobile ? { padding: "28px 20px", borderRadius: 22 } : {}),
            }}>
              <div style={styles.cardSheen} />
              <h3 style={{
                ...styles.scoreTitle,
                ...(isMobile ? { fontSize: 18 } : {}),
              }}>전체 유사도 분석 결과</h3>

              <div style={{ display: "flex", justifyContent: "center", marginBottom: isMobile ? 20 : 28 }}>
                <CircleScore value={data.overall.score} isMobile={isMobile} />
              </div>

              <p style={{
                ...styles.interpretText,
                ...(isMobile ? { fontSize: 13, padding: "12px 14px" } : {}),
              }}>
                {data.overall.interpretation || "전체 유사도에 대한 해석이 표시됩니다."}
              </p>

              <div style={styles.actionRow}>
                <button style={styles.smallBtn} onClick={handlePDF} disabled={pdfLoading}>
                  {pdfLoading ? "생성 중..." : "↓ 다운로드"}
                </button>
                <button style={styles.smallBtn}>↗ 공유</button>
              </div>
            </div>
          </section>

          {/* 분석 보고서 */}
          <section>
            <div style={styles.sectionHeader}>
              <div style={styles.titleAccent} />
              <h2 style={{
                ...styles.sectionTitle,
                ...(isMobile ? { fontSize: 22 } : {}),
              }}>분석 보고서</h2>
            </div>
            <div style={styles.cardWrap}>
              <div style={styles.cardGlow} />
              <div style={{
                ...styles.reportCard,
                ...(isMobile ? { padding: "24px 18px", borderRadius: 20 } : {}),
              }}>
                <div style={styles.cardSheen} />

                <div style={styles.reportBlock}>
                  <div style={styles.reportLabel}>📋 분석 개요</div>
                  <p style={styles.reportText}>{data.summary}</p>
                </div>

                <div style={styles.reportBlock}>
                  <div style={styles.reportLabel}>✨ 주요 공통점</div>
                  <ul style={styles.featureList}>
                    {data.key_differences.map((f, i) => (
                      <li key={i} style={styles.featureItem}>
                        <span style={styles.featureBullet}>•</span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <div style={styles.reportLabel}>📊 신체 부위별 평균 유사도</div>
                  <BodyPartsAvg segments={data.segments} />
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* ============ RIGHT COLUMN — 유사 구간 아코디언 ============ */}
        <aside style={styles.rightColumn}>
          <div style={styles.sectionHeader}>
            <div style={styles.titleAccent} />
            <h2 style={{
              ...styles.sectionTitle,
              ...(isMobile ? { fontSize: 22 } : {}),
            }}>
              유사한 구간{" "}
              <span style={styles.countText}>({data.segments.length}개)</span>
            </h2>
          </div>

          <div style={styles.segmentList}>
            {data.segments.map((s) => {
              const isOpen = openId === s.id;
              return (
                <div
                  key={s.id}
                  style={{
                    ...styles.segmentCard,
                    ...(isMobile ? { padding: "14px 14px", borderRadius: 16 } : {}),
                    ...(isOpen ? styles.segmentCardOpen : {}),
                  }}
                >
                  <div style={styles.cardSheen} />

                  <div
                    onClick={() => setOpenId(isOpen ? null : s.id)}
                    style={{
                      ...styles.segmentHeader,
                      ...(isMobile ? { gap: 12 } : {}),
                    }}
                  >
                    <ScoreBadge score={s.score} isMobile={isMobile} />
                    <div style={styles.segmentInfo}>
                      <div style={styles.segmentTitle}>구간 {s.id}</div>
                      <div style={{
                        ...styles.segmentTime,
                        ...(isMobile ? { fontSize: 11 } : {}),
                      }}>
                        A&nbsp;{formatTime(s.video_a)}&nbsp;&nbsp;↔&nbsp;&nbsp;B&nbsp;{formatTime(s.video_b)}
                      </div>
                    </div>
                    <div style={{
                      ...styles.segmentArrow,
                      transform: isOpen ? "rotate(90deg)" : "rotate(0deg)",
                    }}>›</div>
                  </div>

                  {isOpen && (
                    <div style={styles.segmentExpand}>
                      <div style={styles.expandDivider} />

                      <div style={{
                        ...styles.videoGrid,
                        ...(isMobile ? { gridTemplateColumns: "1fr", gap: 12 } : {}),
                      }}>
                        <SegmentVideoBox
                          label="A"
                          src={data.video_url_a}
                          start={s.video_a?.start}
                          end={s.video_a?.end}
                        />
                        <SegmentVideoBox
                          label="B"
                          src={data.video_url_b}
                          start={s.video_b?.start}
                          end={s.video_b?.end}
                        />
                      </div>

                      <p style={{
                        ...styles.expandDesc,
                        ...(isMobile ? { fontSize: 13, padding: "12px 14px" } : {}),
                      }}>{s.description}</p>

                      {s.body_parts && Object.keys(s.body_parts).length > 0 && (
                        <div style={styles.bodyPartsWrap}>
                          {Object.entries(s.body_parts).map(([key, val]) => (
                            <BodyPartBar
                              key={key}
                              label={BODY_PART_LABELS[key] || key}
                              value={val}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>
      </main>
    </div>
  );
}

/* =========================================================
   Sub Components
   ========================================================= */

const CircleScore = ({ value, isMobile }) => {
  const size = isMobile ? 120 : 150;
  const inner = isMobile ? 94 : 118;
  const deg = value * 3.6;
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: `conic-gradient(${C.emerald} ${deg}deg, rgba(200,242,220,0.5) 0)`,
      display: "flex", alignItems: "center", justifyContent: "center",
      boxShadow: `0 8px 30px rgba(46,139,87,0.25)`, flexShrink: 0,
    }}>
      <div style={{
        width: inner, height: inner, borderRadius: "50%",
        background: "linear-gradient(155deg, rgba(255,255,255,0.95), rgba(255,255,255,0.75))",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,1)",
      }}>
        <div style={{
          fontSize: isMobile ? 24 : 30, fontWeight: 700, color: C.deep,
          fontFamily: "'Chakra Petch',sans-serif", letterSpacing: -1,
        }}>
          {value}%
        </div>
        <div style={{ fontSize: 11, color: C.emerald, marginTop: 2 }}>유사도</div>
      </div>
    </div>
  );
};

const ScoreBadge = ({ score, isMobile }) => {
  const size = isMobile ? 46 : 56;
  const inner = isMobile ? 36 : 44;
  const deg = score * 3.6;
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%", flexShrink: 0,
      background: `conic-gradient(${C.emerald} ${deg}deg, rgba(200,242,220,0.5) 0)`,
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{
        width: inner, height: inner, borderRadius: "50%",
        background: "linear-gradient(155deg, rgba(255,255,255,0.95), rgba(255,255,255,0.8))",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontWeight: 700, color: C.deep, fontSize: isMobile ? 11 : 13,
        fontFamily: "'Chakra Petch',sans-serif",
      }}>
        {score}%
      </div>
    </div>
  );
};

const SegmentVideoBox = ({ label, src, start, end }) => {
  const ref = useRef(null);

  useEffect(() => {
    const video = ref.current;
    if (!video || !src || start == null || end == null) return;

    const onLoaded = () => { video.currentTime = start; };
    const onTimeUpdate = () => {
      if (video.currentTime >= end) video.currentTime = start;
    };

    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("timeupdate", onTimeUpdate);

    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("timeupdate", onTimeUpdate);
    };
  }, [src, start, end]);

  return (
    <div>
      <div style={styles.videoLabelRow}>
        <span style={styles.videoLabelBadge}>{label}</span>
        <span style={styles.videoTime}>{formatTime({ start, end })}</span>
      </div>
      <div style={styles.videoFrame}>
        {src ? (
          <video
            ref={ref}
            src={src}
            autoPlay
            muted
            playsInline
            style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: 12 }}
          />
        ) : (
          <div style={styles.videoPlaceholder}>
            <div style={{ fontSize: 36, opacity: 0.4 }}>▶</div>
            <div style={{ fontSize: 12, color: C.textSoft, marginTop: 8 }}>영상 {label}</div>
          </div>
        )}
      </div>
    </div>
  );
};

const BodyPartBar = ({ label, value }) => {
  const pct = Math.round(value * 100);
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 13, color: C.text, fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: 13, color: C.emerald, fontWeight: 700 }}>{pct}%</span>
      </div>
      <div style={{ height: 5, borderRadius: 999, background: "rgba(46,139,87,0.12)", overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${pct}%`, borderRadius: 999,
          background: `linear-gradient(90deg,${C.forest},${C.emerald},${C.mint})`,
          boxShadow: `0 0 8px ${C.mint}`,
          transition: "width 0.6s ease",
        }} />
      </div>
    </div>
  );
};

const BodyPartsAvg = ({ segments }) => {
  if (!segments || segments.length === 0) return null;

  const keys = Object.keys(BODY_PART_LABELS);
  const avgs = {};
  keys.forEach((k) => {
    const vals = segments.map((s) => s.body_parts?.[k] ?? 0).filter((v) => v > 0);
    avgs[k] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  });

  return (
    <div style={{ marginTop: 4 }}>
      {keys.map((k) => (
        <BodyPartBar key={k} label={BODY_PART_LABELS[k]} value={avgs[k]} />
      ))}
    </div>
  );
};

/* =========================================================
   Styles
   ========================================================= */
const styles = {
  root: {
    position: "relative", minHeight: "100vh", width: "100%",
    overflow: "hidden", fontFamily: "'Rajdhani','Chakra Petch',sans-serif",
    color: C.text, boxSizing: "border-box",
  },
  bgLayer: {
    position: "fixed", inset: 0, zIndex: 0,
    backgroundImage: `url(${bgImage})`, backgroundSize: "cover",
    backgroundPosition: "center", backgroundRepeat: "no-repeat",
  },
  bgTint: {
    position: "fixed", inset: 0, zIndex: 0,
    background: "radial-gradient(1200px 600px at 80% 30%, rgba(255,255,255,0.3), transparent 60%), radial-gradient(900px 500px at 20% 80%, rgba(46,139,87,0.06), transparent 60%)",
    pointerEvents: "none",
  },
  navWrap: {
    position: "fixed", top: 24, left: 0, right: 0,
    display: "flex", justifyContent: "center", zIndex: 10,
  },
  navGlow: {
    position: "absolute", inset: -20,
    background: `radial-gradient(circle at 50% 50%, ${C.mint}40, transparent 70%)`,
    filter: "blur(30px)",
  },
  nav: {
    position: "relative", display: "flex", gap: 4, padding: 6,
    borderRadius: 999,
    background: "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(28px) saturate(180%)", WebkitBackdropFilter: "blur(28px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 20px 50px rgba(11,59,46,0.18)", "0 6px 20px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.95)", "inset 0 -1px 0 rgba(46,139,87,0.12)",
    ].join(", "),
    overflow: "hidden",
  },
  navBtn: {
    padding: "12px 32px", borderRadius: 999, border: "none", cursor: "pointer",
    background: "transparent", color: C.forest, fontFamily: "'Rajdhani',sans-serif",
    fontSize: 15, fontWeight: 700, letterSpacing: 0.5, transition: "all 0.3s",
  },
  navBtnActive: {
    color: "#fff",
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 50%,${C.emerald} 100%)`,
    boxShadow: `0 8px 22px rgba(46,139,87,0.4), inset 0 1px 0 rgba(255,255,255,0.3)`,
  },
  cardSheen: {
    position: "absolute", top: 0, left: 0, right: 0, height: 1, pointerEvents: "none",
    background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
  },
  main: {
    position: "relative", zIndex: 1, padding: "120px 5% 60px",
    display: "grid", gridTemplateColumns: "minmax(0, 1.15fr) minmax(0, 1fr)",
    gap: 36, alignItems: "start", maxWidth: 1500, margin: "0 auto",
  },
  leftColumn: { display: "flex", flexDirection: "column", gap: 32, minWidth: 0 },
  rightColumn: { minWidth: 0 },
  cardWrap: { position: "relative" },
  cardGlow: {
    position: "absolute", inset: -25,
    background: `radial-gradient(ellipse at 50% 50%, ${C.mint}35, transparent 65%)`,
    filter: "blur(45px)", zIndex: 0,
  },
  scoreCard: {
    position: "relative", zIndex: 1, padding: "36px 40px", borderRadius: 28,
    background: "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 50%, rgba(200,242,220,0.3) 100%)",
    backdropFilter: "blur(36px) saturate(180%)", WebkitBackdropFilter: "blur(36px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 30px 80px rgba(11,59,46,0.18)", "0 8px 24px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.95)", "inset 0 -1px 0 rgba(46,139,87,0.12)",
    ].join(", "),
    overflow: "hidden",
  },
  scoreTitle: {
    textAlign: "center", color: C.deep, fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 20, fontWeight: 700, margin: "0 0 24px", letterSpacing: -0.3,
  },
  interpretText: {
    fontSize: 15, color: C.text, lineHeight: 1.85, margin: "0 0 24px",
    fontWeight: 500, letterSpacing: 0.1,
    padding: "16px 20px", borderRadius: 14,
    background: "rgba(255,255,255,0.55)",
    border: "1px solid rgba(46,139,87,0.12)",
  },
  actionRow: { display: "flex", gap: 12, justifyContent: "center", marginTop: 28 },
  smallBtn: {
    padding: "11px 22px", borderRadius: 999, border: "1px solid rgba(255,255,255,0.85)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.65), rgba(255,255,255,0.3))",
    color: C.forest, fontFamily: "'Rajdhani',sans-serif", fontWeight: 700,
    fontSize: 13, cursor: "pointer",
    boxShadow: "0 4px 12px rgba(11,59,46,0.06), inset 0 1px 0 rgba(255,255,255,0.9)",
  },
  sectionHeader: { display: "flex", alignItems: "center", gap: 14, marginBottom: 22 },
  titleAccent: {
    width: 4, height: 32, borderRadius: 4,
    background: `linear-gradient(180deg,${C.forest},${C.mint})`,
    boxShadow: `0 0 18px ${C.mint}`,
  },
  sectionTitle: {
    fontFamily: "'Chakra Petch',sans-serif", fontSize: 28, fontWeight: 700,
    color: C.deep, margin: 0, letterSpacing: -0.5,
  },
  countText: { fontSize: 18, color: C.emerald, fontWeight: 700 },
  reportCard: {
    position: "relative", zIndex: 1, padding: "32px 36px", borderRadius: 24,
    background: "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(28px) saturate(170%)", WebkitBackdropFilter: "blur(28px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: ["0 18px 50px rgba(11,59,46,0.13)", "inset 0 1px 0 rgba(255,255,255,0.95)"].join(", "),
    overflow: "hidden",
  },
  reportBlock: { marginBottom: 24 },
  reportLabel: {
    fontSize: 16, fontWeight: 700, color: C.deep, marginBottom: 14,
    fontFamily: "'Chakra Petch',sans-serif",
  },
  reportText: { fontSize: 15, color: C.text, lineHeight: 1.85, margin: 0, fontWeight: 500 },
  featureList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 10 },
  featureItem: { fontSize: 14, color: C.text, display: "flex", gap: 10, lineHeight: 1.7, fontWeight: 500 },
  featureBullet: { color: C.emerald, fontWeight: 700, flexShrink: 0, fontSize: 16 },
  segmentList: { display: "flex", flexDirection: "column", gap: 14 },
  segmentCard: {
    position: "relative", padding: "18px 22px", borderRadius: 20,
    background: "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(24px) saturate(170%)", WebkitBackdropFilter: "blur(24px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: ["0 12px 32px rgba(11,59,46,0.1)", "inset 0 1px 0 rgba(255,255,255,0.95)"].join(", "),
    transition: "all 0.3s", overflow: "hidden",
  },
  segmentCardOpen: {
    background: "linear-gradient(155deg, rgba(255,255,255,0.85) 0%, rgba(200,242,220,0.5) 100%)",
    boxShadow: [
      "0 18px 44px rgba(46,139,87,0.22)",
      "inset 0 1px 0 rgba(255,255,255,1)",
      `0 0 0 1.5px ${C.mint}`,
    ].join(", "),
  },
  segmentHeader: { display: "flex", alignItems: "center", gap: 18, cursor: "pointer" },
  segmentInfo: { flex: 1, minWidth: 0 },
  segmentTitle: {
    fontWeight: 700, color: C.deep, fontFamily: "'Chakra Petch',sans-serif", fontSize: 17,
  },
  segmentTime: { fontSize: 13, color: C.emerald, margin: "5px 0 0", fontWeight: 700 },
  segmentArrow: {
    color: C.emerald, fontSize: 22, fontWeight: 700,
    flexShrink: 0, transition: "transform 0.3s",
  },
  segmentExpand: { marginTop: 18, animation: "expandDown 0.35s ease-out" },
  expandDivider: {
    height: 1, marginBottom: 18,
    background: "linear-gradient(90deg, transparent, rgba(46,139,87,0.3), transparent)",
  },
  videoGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  videoLabelRow: { display: "flex", alignItems: "center", gap: 10, marginBottom: 8 },
  videoLabelBadge: {
    width: 24, height: 24, borderRadius: 7,
    background: `linear-gradient(135deg,${C.deep},${C.emerald})`,
    color: "#fff", fontSize: 11, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center",
    boxShadow: "0 3px 8px rgba(46,139,87,0.3)",
  },
  videoTime: { fontSize: 11, color: C.emerald, fontWeight: 600 },
  videoFrame: {
    width: "100%", aspectRatio: "16/9", borderRadius: 12, overflow: "hidden",
    background: "rgba(11,59,46,0.15)", border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: "0 6px 16px rgba(11,59,46,0.1), inset 0 1px 0 rgba(255,255,255,0.5)",
  },
  videoPlaceholder: {
    width: "100%", height: "100%", display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center", color: C.emerald,
  },
  expandDesc: {
    fontSize: 14, color: C.text, lineHeight: 1.85,
    margin: "18px 0 16px", padding: "16px 18px",
    borderRadius: 12, fontWeight: 500,
    background: "rgba(255,255,255,0.6)",
    border: "1px solid rgba(46,139,87,0.15)",
  },
  bodyPartsWrap: { marginTop: 4 },
};