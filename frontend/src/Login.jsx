import React, { useState } from "react";
import bgImage from "./assets/background.png";
import { supabase } from "./lib/supabaseClient";
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

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(false);
  const [signupName, setSignupName] = useState("");
  const [pwConfirm, setPwConfirm] = useState("");
  
  // ⭐ 로그인/회원가입 모드 전환
  const [mode, setMode] = useState("login"); // "login" or "signup"
  const isMobile = useIsMobile();

  // 이메일 로그인
  const handleLogin = async () => {
    if (!email || !pw) {
      alert("이메일과 비밀번호를 모두 입력해주세요.");
      return;
    }
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: pw,
    });
    if (error) {
      alert(error.message);
      return;
    }
    onLogin && onLogin();
  };

  // 이메일 회원가입
  const handleSignUp = async () => {
    if (!signupName || !email || !pw || !pwConfirm) {
      alert("모든 항목을 입력해주세요.");
      return;
    }
    if (pw !== pwConfirm) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (pw.length < 6) {
      alert("비밀번호는 최소 6자 이상이어야 합니다.");
      return;
    }
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: pw,
      options: {
        data: { user_name: signupName },
      },
    });
    if (error) {
      console.error("회원가입 에러:", error);
      alert(`회원가입 실패: ${error.message}`);
      return;
    }
    if (data?.user) {
      await supabase.from("profiles").upsert({
        id: data.user.id,
        user_name: signupName,
      });
    }
    alert("회원가입 성공! 이메일을 확인하여 계정을 활성화해주세요.");
    setSignupName("");
    setPwConfirm("");
    setMode("login");
  };


  // ⭐⭐⭐ 구글 로그인/회원가입
  const handleGoogleAuth = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    });
    if (error) {
      alert(error.message);
      return;
    }
  };

  // 주 액션 버튼 핸들러
  const handlePrimaryAction = () => {
    if (mode === "login") {
      handleLogin();
    } else {
      handleSignUp();
    }
  };

  return (
    <div style={{
      ...styles.root,
      ...(isMobile ? {
        gridTemplateColumns: "1fr",
        padding: "0 5%",
        gap: 0,
        alignItems: "center",
        justifyItems: "center",
      } : {}),
    }}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
        rel="stylesheet"
      />
      <div style={styles.bgLayer} />
      <div style={styles.bgTint} />
      {!isMobile && (
      <div style={styles.left}>
        <div style={styles.badge}>
          <span style={styles.badgeDot} />
          AI · DANCE ANALYSIS STUDIO
        </div>
        <h1 style={styles.title}>
          K-pop
          <br />
          <span style={styles.titleGradient}>Visual Studio</span>
        </h1>
        <p style={styles.subtitle}>
          두 K-pop 뮤직비디오를 업로드하면 AI가 유사한 구간을
          <br />
          자동으로 탐지하고 상세한 분석 보고서를 생성합니다.
        </p>
        <div style={styles.statsRow}>
          {[
            ["98%", "정확도"],
            ["12K+", "분석 완료"],
            ["5초", "평균 처리"],
          ].map(([n, l]) => (
            <div key={l} style={styles.statBox}>
              <div style={styles.statNum}>{n}</div>
              <div style={styles.statLabel}>{l}</div>
            </div>
          ))}
        </div>
      </div>
      )}
      <div style={{
        ...styles.cardWrap,
        ...(isMobile ? { width: "100%", justifySelf: "center" } : {}),
      }}>
        <div style={styles.cardGlow} />
        <div style={{
          ...styles.card,
          ...(isMobile ? { padding: "36px 24px 28px", borderRadius: 24 } : {}),
        }}>
          <div style={styles.cardSheen} />
          <div style={styles.cardAccent} />
          <div style={styles.cardHeader}>
            <h2 style={{
              ...styles.cardTitle,
              ...(isMobile ? { fontSize: 28 } : {}),
            }}>
              {mode === "login" ? "로그인" : "회원가입"}
            </h2>
            <p style={styles.cardSub}>
              {mode === "login"
                ? "계정에 로그인하여 분석을 시작하세요"
                : "새 계정을 만들어 분석을 시작하세요"}
            </p>
          </div>
          {mode === "signup" && (
            <Field label="닉네임">
              <InputBox
                icon="👤"
                type="text"
                placeholder="사용할 닉네임"
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handlePrimaryAction()}
              />
            </Field>
          )}
          <Field label="이메일">
            <InputBox
              icon="✉"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handlePrimaryAction()}
            />
          </Field>
          <Field label="비밀번호">
            <InputBox
              icon="🔒"
              type={showPw ? "text" : "password"}
              placeholder={mode === "signup" ? "최소 6자 이상" : "••••••••"}
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handlePrimaryAction()}
              right={
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  style={styles.eyeBtn}
                >
                  {showPw ? "🙈" : "👁"}
                </button>
              }
            />
          </Field>
          {mode === "signup" && (
            <>
              <Field label="비밀번호 확인">
                <InputBox
                  icon="🔒"
                  type={showPw ? "text" : "password"}
                  placeholder="비밀번호 재입력"
                  value={pwConfirm}
                  onChange={(e) => setPwConfirm(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handlePrimaryAction()}
                />
                {pwConfirm && pw !== pwConfirm && (
                  <div style={styles.errorHint}>비밀번호가 일치하지 않습니다</div>
                )}
              </Field>
            </>
          )}


          {/* 로그인 모드일 때만 표시 */}
          {mode === "login" && (
            <div style={styles.optionsRow}>
              <label style={styles.checkLabel}>
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  style={styles.checkbox}
                />
                로그인 상태 유지
              </label>
              <a style={styles.link}>비밀번호 찾기</a>
            </div>
          )}

          {/* 회원가입 모드일 때 추가 안내 */}
          {mode === "signup" && (
            <div style={styles.signupNotice}>
              회원가입 후 이메일 인증이 필요합니다.
            </div>
          )}

          <button style={styles.primaryBtn} onClick={handlePrimaryAction}>
            {mode === "login" ? "로그인" : "회원가입"}
            <span style={{ marginLeft: 8 }}>→</span>
          </button>

          <div style={styles.divider}>
            <span style={styles.dividerLine} />
            <span style={styles.dividerText}>또는</span>
            <span style={styles.dividerLine} />
          </div>

          {/* ⭐⭐⭐ 구글 로그인 버튼에 onClick 연결 */}
          <button style={styles.googleBtn} onClick={handleGoogleAuth}>
            <span style={{ fontSize: 16, marginRight: 8 }}>G</span>
            Google로 {mode === "login" ? "로그인" : "회원가입"}
          </button>

          {/* 모드 전환 링크 */}
          <p style={styles.footerText}>
            {mode === "login" ? (
              <>
                계정이 없으신가요?{" "}
                <a style={styles.linkBold} onClick={() => setMode("signup")}>
                  회원가입
                </a>
              </>
            ) : (
              <>
                이미 계정이 있으신가요?{" "}
                <a style={styles.linkBold} onClick={() => setMode("login")}>
                  로그인
                </a>
              </>
            )}
          </p>

          <p style={styles.terms}>
            계속 진행함으로써 당사의 <u>이용약관</u>과 <u>개인정보처리방침</u>에
            동의합니다.
          </p>
        </div>
      </div>
    </div>
  );
}

const Field = ({ label, children }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={styles.fieldLabel}>{label}</div>
    {children}
  </div>
);

const InputBox = ({ icon, right, ...props }) => (
  <div style={styles.inputWrap}>
    <span style={styles.inputIcon}>{icon}</span>
    <input {...props} style={styles.input} />
    {right && <div style={styles.inputRight}>{right}</div>}
  </div>
);

const styles = {
  root: {
    position: "relative",
    minHeight: "100vh",
    width: "100%",
    overflow: "hidden",
    fontFamily: "'Rajdhani','Chakra Petch',sans-serif",
    color: C.text,
    display: "grid",
    gridTemplateColumns: "1.1fr 1fr",
    alignItems: "center",
    padding: "0 7%",
    gap: 60,
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
      "radial-gradient(1200px 600px at 80% 30%, rgba(255,255,255,0.35), transparent 60%), radial-gradient(900px 500px at 20% 80%, rgba(46,139,87,0.08), transparent 60%)",
    pointerEvents: "none",
  },
  left: {
    position: "relative",
    zIndex: 1,
    paddingBottom: "10vh",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 18px",
    borderRadius: 999,
    background: "rgba(255,255,255,0.55)",
    backdropFilter: "blur(14px) saturate(160%)",
    WebkitBackdropFilter: "blur(14px) saturate(160%)",
    border: "1px solid rgba(255,255,255,0.7)",
    boxShadow: "0 4px 20px rgba(11,59,46,0.08)",
    color: C.forest,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 1.5,
    marginBottom: 28,
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: `linear-gradient(135deg,${C.emerald},${C.mint})`,
    boxShadow: `0 0 10px ${C.mint}`,
  },
  title: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 76,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -2.5,
    lineHeight: 1.02,
  },
  titleGradient: {
    background: `linear-gradient(135deg,${C.forest} 0%,${C.emerald} 50%,${C.emeraldLight} 100%)`,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  subtitle: {
    color: C.textSoft,
    fontSize: 17,
    marginTop: 26,
    lineHeight: 1.75,
    maxWidth: 480,
  },
  statsRow: { display: "flex", gap: 36, marginTop: 40 },
  statBox: {
    paddingLeft: 14,
    borderLeft: `2px solid ${C.mint}`,
  },
  statNum: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 30,
    fontWeight: 700,
    color: C.deep,
    letterSpacing: -0.5,
  },
  statLabel: {
    fontSize: 12,
    color: C.textSoft,
    letterSpacing: 0.8,
    marginTop: 2,
  },
  cardWrap: {
    position: "relative",
    zIndex: 1,
    justifySelf: "end",
    width: 440,
  },
  cardGlow: {
    position: "absolute",
    inset: -40,
    background: `radial-gradient(circle at 50% 50%, ${C.mint}55, transparent 65%)`,
    filter: "blur(40px)",
    zIndex: 0,
  },
  card: {
    position: "relative",
    zIndex: 1,
    padding: "48px 44px 36px",
    borderRadius: 32,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 50%, rgba(200,242,220,0.35) 100%)",
    backdropFilter: "blur(36px) saturate(180%)",
    WebkitBackdropFilter: "blur(36px) saturate(180%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 30px 80px rgba(11,59,46,0.22)",
      "0 8px 24px rgba(11,59,46,0.08)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.15)",
      "inset 1px 0 0 rgba(255,255,255,0.5)",
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
  cardAccent: {
    position: "absolute",
    left: 0,
    top: 48,
    width: 3,
    height: 38,
    borderRadius: "0 4px 4px 0",
    background: `linear-gradient(180deg,${C.forest},${C.mint})`,
    boxShadow: `0 0 20px ${C.mint}`,
  },
  cardHeader: { marginBottom: 28, paddingLeft: 6 },
  cardTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 34,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.5,
  },
  cardSub: {
    color: C.textSoft,
    fontSize: 13,
    margin: "8px 0 0",
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: 700,
    color: C.deep,
    marginBottom: 8,
    letterSpacing: 0.3,
  },
  inputWrap: {
    position: "relative",
    background:
      "linear-gradient(135deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4))",
    border: "1px solid rgba(255,255,255,0.9)",
    borderRadius: 14,
    boxShadow:
      "inset 0 1px 2px rgba(11,59,46,0.06), 0 2px 8px rgba(11,59,46,0.05)",
    transition: "all 0.2s",
  },
  inputIcon: {
    position: "absolute",
    left: 16,
    top: "50%",
    transform: "translateY(-50%)",
    color: C.emerald,
    fontSize: 14,
  },
  input: {
    width: "100%",
    padding: "15px 44px 15px 44px",
    border: "none",
    background: "transparent",
    fontSize: 14,
    color: C.text,
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "inherit",
  },
  inputRight: {
    position: "absolute",
    right: 8,
    top: "50%",
    transform: "translateY(-50%)",
  },
  eyeBtn: {
    background: "transparent",
    border: "none",
    cursor: "pointer",
    fontSize: 14,
    padding: 6,
    color: C.textSoft,
  },
  optionsRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    margin: "18px 0 24px",
    fontSize: 13,
    color: C.textSoft,
  },
  checkLabel: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    cursor: "pointer",
  },
  checkbox: { accentColor: C.emerald, width: 14, height: 14 },
  link: { color: C.emerald, cursor: "pointer", fontWeight: 600 },
  linkBold: { color: C.emerald, cursor: "pointer", fontWeight: 700 },
  signupNotice: {
    fontSize: 12,
    color: C.textSoft,
    marginTop: -8,
    marginBottom: 24,
    padding: "10px 14px",
    background: "rgba(46,139,87,0.08)",
    borderRadius: 8,
    borderLeft: `3px solid ${C.emerald}`,
  },
  errorHint: {
  fontSize: 11,
  color: "#D32F2F",
  marginTop: 6,
  paddingLeft: 4,
  fontWeight: 600,
},
  primaryBtn: {
    width: "100%",
    padding: "16px",
    borderRadius: 999,
    border: "none",
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 40%,${C.emerald} 100%)`,
    color: "#fff",
    fontSize: 15,
    fontWeight: 700,
    letterSpacing: 0.5,
    cursor: "pointer",
    fontFamily: "'Rajdhani',sans-serif",
    boxShadow: `0 12px 30px rgba(46,139,87,0.4), inset 0 1px 0 rgba(255,255,255,0.3)`,
    transition: "transform 0.15s",
  },
  divider: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    margin: "22px 0",
  },
  dividerLine: {
    flex: 1,
    height: 1,
    background:
      "linear-gradient(90deg, transparent, rgba(46,139,87,0.3), transparent)",
  },
  dividerText: { color: C.textSoft, fontSize: 12 },
  googleBtn: {
    width: "100%",
    padding: "14px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.9)",
    background:
      "linear-gradient(135deg, rgba(255,255,255,0.6), rgba(255,255,255,0.3))",
    backdropFilter: "blur(10px)",
    color: C.deep,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
    boxShadow: "0 4px 12px rgba(11,59,46,0.06)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s",
  },
  footerText: {
    textAlign: "center",
    color: C.textSoft,
    fontSize: 13,
    marginTop: 22,
    marginBottom: 8,
  },
  terms: {
    textAlign: "center",
    color: C.textSoft,
    fontSize: 11,
    margin: 0,
    opacity: 0.8,
  },
};
