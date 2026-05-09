import React, { useState } from "react";

import bgImage from "./assets/profile_background.png";

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

const FEATURES = [
  {
    icon: "🎯",
    title: "정밀한 안무 분석",
    desc: "딥러닝 기반 포즈 추정으로 신체 관절 단위까지 분석하여, 두 영상의 움직임을 정확하게 비교합니다.",
  },
  {
    icon: "⚡",
    title: "빠른 처리 속도",
    desc: "최적화된 알고리즘으로 평균 60초 이내에 분석을 완료해 빠르게 결과를 확인할 수 있습니다.",
  },
  {
    icon: "📊",
    title: "구간별 상세 리포트",
    desc: "전체 유사도뿐 아니라 구간별 일치 패턴, 동작 특성, 타이밍까지 시각화해 한눈에 파악할 수 있습니다.",
  },
  {
    icon: "🔒",
    title: "안전한 데이터 보관",
    desc: "업로드된 영상과 분석 결과는 암호화되어 저장되며, 사용자만 접근할 수 있도록 보호됩니다.",
  },
];

const STEPS = [
  { n: "01", title: "영상 업로드", desc: "비교할 두 K-pop 안무 영상을 드래그하거나 클릭해서 업로드합니다." },
  { n: "02", title: "AI 분석 실행", desc: "딥러닝 모델이 두 영상의 움직임 패턴과 타이밍을 자동으로 분석합니다." },
  { n: "03", title: "결과 확인", desc: "유사 구간, 일치율, 상세 리포트를 통해 분석 결과를 확인하고 공유할 수 있습니다." },
];

export default function AboutUsPage({ onNavigate, isLoggedIn }) {
  const [activeNav, setActiveNav] = useState("about");

  return (
    <div style={styles.root}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
        rel="stylesheet"
      />

      <div style={styles.bgLayer} />
      <div style={styles.bgTint} />

      {/* ===== Top Navigation — 로그인 상태에서만 표시 ===== */}
      {isLoggedIn && (
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
                  style={{ ...styles.navBtn, ...(active ? styles.navBtnActive : {}) }}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>
      )}

      {/* ===== Main Content ===== */}
      <main style={styles.main}>
        {/* ----- HERO ----- */}
        <section style={styles.heroWrap}>
          <div style={styles.heroGlow} />
          <div style={styles.heroCard}>
            <div style={styles.cardSheen} />

            <div style={styles.badge}>
              <span style={styles.badgeDot} />
              ABOUT&nbsp;K-POP&nbsp;VISUAL&nbsp;STUDIO
            </div>

            <h1 style={styles.heroTitle}>
              안무를 데이터로,
              <br />
              <span style={styles.titleGradient}>춤을 과학으로</span>
            </h1>

            <p style={styles.heroDesc}>
              K-pop Visual Studio는 AI 기반 영상 분석 기술로 두 안무의 유사도를 정밀하게 측정하는 서비스입니다.
              <br />
              안무 창작자, 댄서, 그리고 K-pop을 사랑하는 모든 사람들을 위해 만들어졌습니다.
            </p>

            <div style={styles.statRow}>
              {[
                ["70 %", "분석 정확도"],
                ["12K+", "누적 분석"],
                ["60초", "평균 처리"],
                ["24/7", "서비스 운영"],
              ].map(([n, l]) => (
                <div key={l} style={styles.statBox}>
                  <div style={styles.statNum}>{n}</div>
                  <div style={styles.statLabel}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ----- MISSION ----- */}
        <section style={styles.sectionHeader}>
          <div style={styles.titleAccent} />
          <div>
            <div style={styles.sectionEyebrow}>OUR MISSION</div>
            <h2 style={styles.sectionTitle}>우리가 만드는 가치</h2>
          </div>
        </section>

        <div style={styles.featureGrid}>
          {FEATURES.map((f) => (
            <div key={f.title} style={styles.featureCard}>
              <div style={styles.cardSheen} />
              <div style={styles.featureIcon}>{f.icon}</div>
              <div style={styles.featureTitle}>{f.title}</div>
              <p style={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </div>

        {/* ----- HOW IT WORKS ----- */}
        <section style={{ ...styles.sectionHeader, marginTop: 60 }}>
          <div style={styles.titleAccent} />
          <div>
            <div style={styles.sectionEyebrow}>HOW IT WORKS</div>
            <h2 style={styles.sectionTitle}>사용 방법</h2>
          </div>
        </section>

        <div style={styles.stepGrid}>
          {STEPS.map((s, i) => (
            <React.Fragment key={s.n}>
              <div style={styles.stepCard}>
                <div style={styles.cardSheen} />
                <div style={styles.stepNum}>{s.n}</div>
                <div style={styles.stepTitle}>{s.title}</div>
                <p style={styles.stepDesc}>{s.desc}</p>
              </div>
              {i < STEPS.length - 1 && <div style={styles.stepConnector}>→</div>}
            </React.Fragment>
          ))}
        </div>

        {/* ----- CTA ----- */}
        <section style={styles.ctaWrap}>
          <div style={styles.ctaGlow} />
          <div style={styles.ctaCard}>
            <div style={styles.cardSheen} />
            <h3 style={styles.ctaTitle}>지금 바로 시작해보세요</h3>
            <p style={styles.ctaDesc}>
              두 영상을 업로드하는 것만으로 AI 기반 안무 분석이 시작됩니다.
            </p>
            <button style={styles.ctaBtn} onClick={() => onNavigate && onNavigate(isLoggedIn ? "analyse" : "login")}>
              <span style={{ marginRight: 10 }}>✦</span>
              {isLoggedIn ? "분석 시작하기" : "로그인하고 시작하기"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

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
    background: "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 100%)",
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
    top: 0, left: 0, right: 0, height: 1,
    background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
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

  /* ----- Main ----- */
  main: {
    position: "relative",
    zIndex: 1,
    padding: "120px 8% 80px",
    maxWidth: 1280,
    margin: "0 auto",
  },

  /* ----- Hero ----- */
  heroWrap: { position: "relative", marginBottom: 60 },
  heroGlow: {
    position: "absolute",
    inset: -30,
    background: `radial-gradient(ellipse at 50% 50%, ${C.mint}40, transparent 65%)`,
    filter: "blur(50px)",
    zIndex: 0,
  },
  heroCard: {
    position: "relative",
    zIndex: 1,
    padding: "56px 60px",
    borderRadius: 36,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 50%, rgba(200,242,220,0.3) 100%)",
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
    textAlign: "center",
  },
  cardSheen: {
    position: "absolute",
    top: 0, left: 0, right: 0, height: 1,
    background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
    pointerEvents: "none",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 20px",
    borderRadius: 999,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.8)",
    color: C.forest,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 1.5,
    marginBottom: 24,
    boxShadow: "0 4px 14px rgba(46,139,87,0.18)",
  },
  badgeDot: {
    width: 6, height: 6,
    borderRadius: "50%",
    background: `linear-gradient(135deg,${C.emerald},${C.mint})`,
    boxShadow: `0 0 10px ${C.mint}`,
  },
  heroTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 56,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -2,
    lineHeight: 1.1,
  },
  titleGradient: {
    background: `linear-gradient(135deg,${C.forest} 0%,${C.emerald} 50%,${C.emeraldLight} 100%)`,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  heroDesc: {
    color: C.textSoft,
    fontSize: 16,
    lineHeight: 1.8,
    margin: "24px auto 36px",
    maxWidth: 680,
  },
  statRow: {
    display: "flex",
    justifyContent: "center",
    gap: 50,
    flexWrap: "wrap",
    paddingTop: 28,
    borderTop: "1px solid rgba(46,139,87,0.15)",
  },
  statBox: { textAlign: "center" },
  statNum: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 32,
    fontWeight: 700,
    background: `linear-gradient(135deg,${C.forest},${C.emerald})`,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
    letterSpacing: -0.5,
  },
  statLabel: { fontSize: 12, color: C.textSoft, letterSpacing: 0.8, marginTop: 4 },

  /* ----- Section header ----- */
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    marginBottom: 24,
  },
  titleAccent: {
    width: 4, height: 44,
    borderRadius: 4,
    background: `linear-gradient(180deg,${C.forest},${C.mint})`,
    boxShadow: `0 0 18px ${C.mint}`,
  },
  sectionEyebrow: {
    fontSize: 11,
    fontWeight: 700,
    color: C.emerald,
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  sectionTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 28,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.5,
  },

  /* ----- Feature grid ----- */
  featureGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 20,
  },
  featureCard: {
    position: "relative",
    padding: "28px 28px",
    borderRadius: 22,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(28px) saturate(170%)",
    WebkitBackdropFilter: "blur(28px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 16px 40px rgba(11,59,46,0.13)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.1)",
    ].join(", "),
    overflow: "hidden",
  },
  featureIcon: {
    width: 50, height: 50,
    borderRadius: 14,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.8)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 24,
    marginBottom: 16,
    boxShadow: "0 4px 14px rgba(46,139,87,0.15)",
  },
  featureTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 18,
    fontWeight: 700,
    color: C.deep,
    marginBottom: 8,
    letterSpacing: -0.3,
  },
  featureDesc: {
    fontSize: 13,
    color: C.textSoft,
    lineHeight: 1.7,
    margin: 0,
  },

  /* ----- Steps ----- */
  stepGrid: {
    display: "flex",
    alignItems: "stretch",
    gap: 16,
  },
  stepCard: {
    flex: 1,
    position: "relative",
    padding: "26px 26px",
    borderRadius: 20,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 100%)",
    backdropFilter: "blur(28px) saturate(170%)",
    WebkitBackdropFilter: "blur(28px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 14px 36px rgba(11,59,46,0.12)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
    ].join(", "),
    overflow: "hidden",
  },
  stepNum: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 32,
    fontWeight: 700,
    background: `linear-gradient(135deg,${C.forest},${C.emerald},${C.mint})`,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
    marginBottom: 10,
    letterSpacing: -1,
  },
  stepTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 17,
    fontWeight: 700,
    color: C.deep,
    marginBottom: 8,
  },
  stepDesc: {
    fontSize: 13,
    color: C.textSoft,
    lineHeight: 1.7,
    margin: 0,
  },
  stepConnector: {
    display: "flex",
    alignItems: "center",
    color: C.emerald,
    fontSize: 22,
    fontWeight: 700,
  },

  /* ----- CTA ----- */
  ctaWrap: { position: "relative", marginTop: 70 },
  ctaGlow: {
    position: "absolute",
    inset: -30,
    background: `radial-gradient(ellipse at 50% 50%, ${C.mint}55, transparent 65%)`,
    filter: "blur(50px)",
    zIndex: 0,
  },
  ctaCard: {
    position: "relative",
    zIndex: 1,
    padding: "44px 50px",
    borderRadius: 28,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(200,242,220,0.4) 100%)",
    backdropFilter: "blur(36px) saturate(180%)",
    WebkitBackdropFilter: "blur(36px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 30px 80px rgba(11,59,46,0.2)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.12)",
    ].join(", "),
    overflow: "hidden",
    textAlign: "center",
  },
  ctaTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 30,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.8,
  },
  ctaDesc: {
    color: C.textSoft,
    fontSize: 15,
    margin: "12px 0 26px",
  },
  ctaBtn: {
    padding: "16px 48px",
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
  },
};