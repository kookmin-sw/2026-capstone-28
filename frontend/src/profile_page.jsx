import React, { useState, useEffect, useRef } from "react";
import { supabase } from "./lib/supabaseClient";

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

export default function ProfilePage({ onNavigate }) {
  const [activeNav, setActiveNav] = useState("profile");
  const [isLoading, setIsLoading] = useState(true);
  const [historyCount, setHistoryCount] = useState(0);
  const [historyItems, setHistoryItems] = useState([]);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [userProfile, setUserProfile] = useState({
    username: "",
    email: "",
    joinDate: "",
    totalAnalyses: 0,
  });
  const [editModalType, setEditModalType] = useState(null); // "profile" | "password" | null
  const [modalLoading, setModalLoading] = useState(false);

  const closeEditModal = () => {
    if (modalLoading) return;
    setEditModalType(null);
  };

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const { data: authData, error: authError } = await supabase.auth.getUser();
        if (authError || !authData?.user) return;

        const authUser = authData.user;

        // ── profiles 테이블에서 username 조회 ──
        const { data: userRow } = await supabase
          .from("profiles")
          .select("user_name")
          .eq("id", authUser.id)
          .single();

        // ── analyses 테이블에서 히스토리 조회 ──
        const { data: analysesData, error: analysesError } = await supabase
          .from("analyses")
          .select("aid, created_at, result_data")
          .eq("user_id", authUser.id)
          .order("created_at", { ascending: false });

        if (!analysesError && analysesData) {
          const parsedHistory = analysesData.map((item) => {
            const rd = item.result_data || {};
            const isCompleted = rd.overall !== undefined;

            return {
              id: item.aid,
              title: `분석 #${item.aid}`,
              date: item.created_at
                ? new Date(item.created_at).toLocaleDateString("ko-KR")
                : "날짜 없음",
              similarity: isCompleted ? (rd.overall?.score ?? 0) : null,
              tag: isCompleted
                ? (rd.key_differences?.[0] || "분석 완료")
                : "분석 중",
              summary: isCompleted
                ? (rd.summary || "요약 없음")
                : "분석이 아직 완료되지 않았습니다.",
              thumbA: rd.video_url_a || null,
              thumbB: rd.video_url_b || null,
              isPending: !isCompleted,

              // ⭐ 모달에서 사용할 상세 데이터
              interpretation: rd.overall?.interpretation || "",
              segments: (rd.segments || []).map((seg) => ({
                id: seg.id,
                timeA: _formatTimeRange(seg.video_a),
                timeB: _formatTimeRange(seg.video_b),
                desc: seg.description || "",
              })),
              keyDifferences: rd.key_differences || [],
            };
          });

          setHistoryItems(parsedHistory);
          setHistoryCount(parsedHistory.length);
        }

        setUserProfile({
          username: userRow?.user_name || "",
          email: authUser.email || "",
          joinDate: authUser.created_at
            ? new Date(authUser.created_at).toLocaleDateString("ko-KR")
            : "",
          totalAnalyses: analysesData?.length || 0,
        });

      } catch (err) {
        console.error("프로필 로드 실패:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);
  const handleDeleteHistory = async (analysisId) => {
    const ok = window.confirm("이 분석 기록을 삭제할까요?");
    if (!ok) return;

    try {
      const { data: authData, error: authError } = await supabase.auth.getUser();
      
      if (authError || !authData?.user) {
        alert("로그인이 필요합니다.");
        return;
      }

      const authUser = authData.user;

      const { error } = await supabase
        .from("analyses")
        .delete()
        .eq("aid", analysisId)
        .eq("user_id", authUser.id);
      
      if (error) {
        console.error("히스토리 삭제 실패:", error);
        alert("히스토리 삭제에 실패했습니다.");
        return;
      }

      setHistoryItems((prev) => prev.filter((item) => item.id !== analysisId));
      setHistoryCount((prev) => Math.max(prev - 1, 0));
      setUserProfile((prev) => ({
        ...prev,
        totalAnalyses: Math.max(prev.totalAnalyses - 1, 0),
      }));

      if (selectedHistory?.id === analysisId) {
        setSelectedHistory(null);
      }
    } catch (err) {
      console.error("히스토리 삭제 중 오류:", err);
      alert("히스토리 삭제 중 오류가 발생했습니다.");
    }
  };

  const verifyCurrentPassword = async (currentPassword) => {
    const { data: authData, error: authError } = await supabase.auth.getUser();

    if (authError || !authData?.user?.email) {
      throw new Error("로그인이 필요합니다.");
    }

    const { error } = await supabase.auth.signInWithPassword({
      email: authData.user.email,
      password: currentPassword,
    });

    if (error) {
      throw new Error("현재 비밀번호가 올바르지 않습니다.");
    }

    return authData.user;
  };

  const handleUpdateProfile = async ({ currentPassword, username }) => {
    const trimmedUsername = username.trim();

    if (!trimmedUsername) {
      alert("변경할 이름을 입력해주세요.");
      return;
    }

    setModalLoading(true);
    try {
      const authUser = await verifyCurrentPassword(currentPassword);

      const { error } = await supabase
        .from("profiles")
        .update({ user_name: trimmedUsername })
        .eq("id", authUser.id);

      if (error) {
        console.error("회원정보 수정 실패:", error);
        alert("회원정보 수정에 실패했습니다.");
        return;
      }

      setUserProfile((prev) => ({
        ...prev,
        username: trimmedUsername,
      }));
      alert("회원정보가 수정되었습니다.");
      setEditModalType(null);
    } catch (err) {
      alert(err.message || "회원정보 수정 중 오류가 발생했습니다.");
    } finally {
      setModalLoading(false);
    }
  };

  const handleUpdatePassword = async ({ currentPassword, newPassword, newPasswordConfirm }) => {
    if (newPassword.length < 6) {
      alert("새 비밀번호는 6자 이상으로 입력해주세요.");
      return;
    }

    if (newPassword !== newPasswordConfirm) {
      alert("새 비밀번호가 서로 일치하지 않습니다.");
      return;
    }

    setModalLoading(true);
    try {
      await verifyCurrentPassword(currentPassword);

      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });

      if (error) {
        console.error("비밀번호 변경 실패:", error);
        alert("비밀번호 변경에 실패했습니다.");
        return;
      }

      alert("비밀번호가 변경되었습니다.");
      setEditModalType(null);
    } catch (err) {
      alert(err.message || "비밀번호 변경 중 오류가 발생했습니다.");
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div style={styles.root}>
      <link
        href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes modalFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes modalSlideUp {
          from { opacity: 0; transform: translateY(30px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

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
                style={{ ...styles.navBtn, ...(active ? styles.navBtnActive : {}) }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* ===== Main Content ===== */}
      <main style={styles.main}>
        {/* ----- LEFT: User Profile Card ----- */}
        <aside style={styles.leftColumn}>
          <div style={styles.cardGlow} />
          <div style={styles.profileCard}>
            <div style={styles.cardSheen} />

            <div style={styles.profileHeader}>
              <div style={styles.avatar}>
                <span style={styles.avatarIcon}>👤</span>
              </div>
              <div>
                <div style={styles.userName}>
                  {userProfile.username || "이름 없음"}
                </div>
                <div style={styles.userHandle}>
                  {userProfile.email || "이메일 없음"}
                </div>
              </div>
            </div>

            <div style={styles.divider} />

            <InfoRow icon="✉" label="이메일" value={userProfile.email || "이메일 없음"} />
            <InfoRow icon="📅" label="가입일" value={userProfile.joinDate || "가입일 없음"} />
            <InfoRow icon="📄" label="총 분석 횟수" value={`${userProfile.totalAnalyses || 0}회`} />

            <div style={styles.divider} />

            <div style={styles.actionRow}>
              <button
                style={styles.actionBtn}
                onClick={() => setEditModalType("profile")}
              >
                정보 수정
              </button>
              <button
                style={styles.actionBtn}
                onClick={() => setEditModalType("password")}
              >
                비밀번호 변경
              </button>
            </div>
          </div>
        </aside>

        {/* ----- RIGHT: History ----- */}
        <section style={styles.rightColumn}>
          <div style={styles.historyHeader}>
            <div style={styles.historyTitleRow}>
              <div style={styles.titleAccent} />
              <h2 style={styles.historyTitle}>분석 히스토리</h2>
            </div>
            <span style={styles.countBadge}>총 {historyCount}건</span>
          </div>

          <div style={styles.historyList}>
            {isLoading ? (
              <div style={styles.loadingWrap}>
                <div style={styles.loadingSpinner} />
                <div style={styles.loadingText}>히스토리 불러오는 중...</div>
              </div>
            ) : historyItems.length === 0 ? (
              <div style={styles.emptyWrap}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>📂</div>
                <div style={styles.emptyText}>아직 분석 기록이 없어요</div>
              </div>
            ) : (
              historyItems.map((item) => (
                <HistoryCard
                  key={item.id}
                  item={item}
                  onDetail={() => setSelectedHistory(item)}
                  onDelete={handleDeleteHistory}
                />
              ))
            )}
          </div>
        </section>
      </main>

      {/* ===== Profile Edit / Password Change Modal ===== */}
      {editModalType && (
        <AccountEditModal
          type={editModalType}
          userProfile={userProfile}
          loading={modalLoading}
          onClose={closeEditModal}
          onSubmit={editModalType === "profile" ? handleUpdateProfile : handleUpdatePassword}
        />
      )}


      {/* ===== Detail Modal ===== */}
      {selectedHistory && (
        <DetailModal
          item={selectedHistory}
          onClose={() => setSelectedHistory(null)}
        />
      )}
    </div>
  );
}

/* ---------- 헬퍼: { start, end } → "00:10 - 00:15" ---------- */
function _formatTimeRange(range) {
  if (!range) return "";
  const fmt = (sec) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };
  return `${fmt(range.start)} - ${fmt(range.end)}`;
}

/* ---------- Sub Components ---------- */
const InfoRow = ({ icon, label, value }) => (
  <div style={styles.infoRow}>
    <div style={styles.infoIcon}>{icon}</div>
    <div>
      <div style={styles.infoLabel}>{label}</div>
      <div style={styles.infoValue}>{value}</div>
    </div>
  </div>
);

const HistoryCard = ({ item, onDetail, onDelete }) => (
  <div style={{
    ...styles.historyCard,
    ...(item.isPending ? styles.historyCardPending : {}),
  }}>
    <div style={styles.cardSheen} />

    <div style={styles.historyTop}>
      <div style={styles.historyTextSide}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h3 style={styles.historyCardTitle}>{item.title}</h3>
          {item.isPending && (
            <span style={styles.pendingBadge}>분석 중</span>
          )}
        </div>
        <div style={styles.historyDate}>📅 {item.date}</div>

        <div style={styles.tagRow}>
          {!item.isPending && (
            <span style={styles.simBadge}>유사 {item.similarity}%</span>
          )}
          <span style={styles.featureBadge}>{item.tag}</span>
        </div>

        <p style={styles.summary}>{item.summary}</p>
      </div>

      <div style={styles.thumbColumn}>
        <ThumbBox label="A" src={item.thumbA} />
        <ThumbBox label="B" src={item.thumbB} />
      </div>
    </div>

    {/* Progress + detail — 완료된 분석만 */}
    {!item.isPending && (
      <>
        <div style={styles.progressTrack}>
          <div style={{ ...styles.progressFill, width: `${item.similarity}%` }} />
        </div>
        <div style={styles.cardFooter}>
          <span style={styles.footerLabel}>유사도 분석 결과</span>

          <div style={styles.footerBtnGroup}>
            <button
              style={styles.deleteBtn}
              onClick={() => onDelete(item.id)}
            >
              히스토리 삭제
            </button>

            <button onClick={onDetail} style={styles.detailBtn}>
              자세히 보기 <span style={{ marginLeft: 4 }}>→</span>
            </button>
          </div>
        </div>
      </>
    )}
  </div>
);

const ThumbBox = ({ label, src }) => {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && src) ref.current.currentTime = 1;
  }, [src]);

  return (
    <div style={styles.thumbBox}>
      {src ? (
        <video
          ref={ref}
          src={src}
          muted
          playsInline
          style={styles.thumbImg}
        />
      ) : (
        <div style={{
          ...styles.thumbImg,
          background: "rgba(11,59,46,0.1)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 20, color: C.emerald,
        }}>▶</div>
      )}
      <div style={styles.thumbLabel}>{label}</div>
    </div>
  );
};

/* ---------- Account Edit Modal ---------- */
const AccountEditModal = ({ type, userProfile, loading, onClose, onSubmit }) => {
  const isProfileEdit = type === "profile";
  const [currentPassword, setCurrentPassword] = useState("");
  const [username, setUsername] = useState(userProfile.username || "");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!currentPassword) {
      alert("현재 비밀번호를 입력해주세요.");
      return;
    }

    onSubmit({
      currentPassword,
      username,
      newPassword,
      newPasswordConfirm,
    });
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <form style={styles.accountModalCard} onSubmit={handleSubmit} onClick={(e) => e.stopPropagation()}>
        <div style={styles.cardSheen} />
        <button type="button" onClick={onClose} style={styles.modalClose} disabled={loading}>✕</button>

        <div style={styles.modalBadge}>
          <span style={styles.modalBadgeDot} />
          {isProfileEdit ? "회원정보 수정" : "비밀번호 변경"}
        </div>

        <h2 style={styles.accountModalTitle}>
          {isProfileEdit ? "회원정보 수정" : "비밀번호 변경"}
        </h2>
        <p style={styles.accountModalDesc}>
          보안을 위해 현재 로그인된 계정의 비밀번호를 먼저 확인합니다.
        </p>

        <div style={styles.formGroup}>
          <label style={styles.formLabel}>이메일</label>
          <input
            value={userProfile.email || ""}
            disabled
            style={{ ...styles.formInput, ...styles.formInputDisabled }}
          />
        </div>

        <div style={styles.formGroup}>
          <label style={styles.formLabel}>현재 비밀번호</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="현재 비밀번호를 입력하세요"
            style={styles.formInput}
            autoComplete="current-password"
          />
        </div>

        {isProfileEdit ? (
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>이름</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="변경할 이름을 입력하세요"
              style={styles.formInput}
            />
          </div>
        ) : (
          <>
            <div style={styles.formGroup}>
              <label style={styles.formLabel}>새 비밀번호</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="새 비밀번호를 입력하세요"
                style={styles.formInput}
                autoComplete="new-password"
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.formLabel}>새 비밀번호 확인</label>
              <input
                type="password"
                value={newPasswordConfirm}
                onChange={(e) => setNewPasswordConfirm(e.target.value)}
                placeholder="새 비밀번호를 한 번 더 입력하세요"
                style={styles.formInput}
                autoComplete="new-password"
              />
            </div>
          </>
        )}

        <div style={styles.modalFooter}>
          <button type="button" onClick={onClose} style={styles.accountCancelBtn} disabled={loading}>
            취소
          </button>
          <button type="submit" style={styles.modalCloseBtn} disabled={loading}>
            {loading ? "처리 중..." : isProfileEdit ? "수정하기" : "변경하기"}
          </button>
        </div>
      </form>
    </div>
  );
};

/* ---------- Detail Modal ---------- */
const DetailModal = ({ item, onClose }) => {
  const deg = (item.similarity || 0) * 3.6;

  const [pdfLoading, setPdfLoading] = useState(false);
    const handlePDF = async () => {
      setPdfLoading(true);
      try {
        await generatePDF(item);
      } finally {
        setPdfLoading(false);
      }
    };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div style={styles.cardSheen} />

        {/* 닫기 버튼 */}
        <button onClick={onClose} style={styles.modalClose}>✕</button>

        {/* ===== 상단: 제목 + 점수 ===== */}
        <div style={styles.modalHeader}>
          <div style={styles.modalTitleArea}>
            <div style={styles.modalBadge}>
              <span style={styles.modalBadgeDot} />
              분석 상세 보기
            </div>
            <h2 style={styles.modalTitle}>{item.title}</h2>
            <div style={styles.modalDate}>📅 {item.date}</div>
          </div>

          {/* 원형 점수 */}
          <div style={{
            width: 100, height: 100, borderRadius: "50%",
            background: `conic-gradient(${C.emerald} ${deg}deg, rgba(200,242,220,0.5) 0)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 6px 20px rgba(46,139,87,0.25)`, flexShrink: 0,
          }}>
            <div style={{
              width: 78, height: 78, borderRadius: "50%",
              background: "linear-gradient(155deg, rgba(255,255,255,0.95), rgba(255,255,255,0.75))",
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
              boxShadow: "inset 0 1px 0 rgba(255,255,255,1)",
            }}>
              <div style={{
                fontSize: 22, fontWeight: 700, color: C.deep,
                fontFamily: "'Chakra Petch',sans-serif", letterSpacing: -1,
              }}>{item.similarity ?? 0}%</div>
              <div style={{ fontSize: 10, color: C.emerald }}>유사도</div>
            </div>
          </div>
        </div>

        <div style={styles.modalDivider} />

        {/* ===== 분석 개요 ===== */}
        <div style={styles.modalSection}>
          <div style={styles.modalSectionLabel}>📋 분석 개요</div>
          <p style={styles.modalText}>
            {item.interpretation || item.summary || "분석 개요가 없습니다."}
          </p>
        </div>

        {/* ===== 유사 구간 ===== */}
        {item.segments && item.segments.length > 0 && (
          <div style={styles.modalSection}>
            <div style={styles.modalSectionLabel}>
              🎬 유사 구간 ({item.segments.length}개)
            </div>
            <div style={styles.modalSegmentList}>
              {item.segments.map((seg) => (
                <div key={seg.id} style={styles.modalSegment}>
                  <div style={styles.modalSegmentHeader}>
                    <span style={styles.modalSegmentBadge}>구간 {seg.id}</span>
                    <span style={styles.modalSegmentTime}>
                      {seg.timeA} ↔ {seg.timeB}
                    </span>
                  </div>
                  <p style={styles.modalSegmentDesc}>{seg.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== 주요 차이점 ===== */}
        {item.keyDifferences && item.keyDifferences.length > 0 && (
          <div style={styles.modalSection}>
            <div style={styles.modalSectionLabel}>⚡ 주요 차이점</div>
            <ul style={styles.modalDiffList}>
              {item.keyDifferences.map((diff, i) => (
                <li key={i} style={styles.modalDiffItem}>
                  <span style={styles.modalDiffBullet}>•</span>
                  {diff}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ===== 하단 닫기 버튼 ===== */}
        <div style={styles.modalFooter}>
          <button onClick={onClose} style={styles.modalCloseBtn}>닫기</button>
          <button onClick={handlePDF} style={styles.modalPdfBtn} disabled={pdfLoading}>
            {pdfLoading ? "생성 중..." : "↓ PDF 저장"}
          </button>
        </div>
      </div>
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

  /* ----- Main grid ----- */
  main: {
    position: "relative",
    zIndex: 1,
    padding: "120px 8% 60px 12%",
    display: "grid",
    gridTemplateColumns: "360px minmax(0, 720px)",
    gap: 40,
    alignItems: "start",
    justifyContent: "center",
  },

  /* ----- LEFT: profile card ----- */
  leftColumn: { position: "relative" },
  cardGlow: {
    position: "absolute",
    inset: -30,
    background: `radial-gradient(circle at 50% 50%, ${C.mint}40, transparent 65%)`,
    filter: "blur(45px)",
    zIndex: 0,
  },
  profileCard: {
    position: "relative",
    zIndex: 1,
    padding: "36px 32px 32px",
    borderRadius: 28,
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
  },
  cardSheen: {
    position: "absolute",
    top: 0, left: 0, right: 0, height: 1,
    background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,1) 50%, transparent 100%)",
    pointerEvents: "none",
  },
  profileHeader: {
    display: "flex",
    alignItems: "center",
    gap: 18,
  },
  avatar: {
    width: 72, height: 72,
    borderRadius: 18,
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 50%,${C.emerald} 100%)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: `0 10px 24px rgba(46,139,87,0.35), inset 0 1px 0 rgba(255,255,255,0.3)`,
  },
  avatarIcon: { fontSize: 32 },
  userName: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 26,
    fontWeight: 700,
    color: C.deep,
    letterSpacing: -0.5,
  },
  userHandle: { fontSize: 13, color: C.textSoft, marginTop: 2 },
  divider: {
    height: 1,
    margin: "24px 0",
    background: "linear-gradient(90deg, transparent, rgba(46,139,87,0.25), transparent)",
  },

  infoRow: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    marginBottom: 18,
  },
  infoIcon: {
    width: 36, height: 36,
    borderRadius: 10,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.7)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 14,
    flexShrink: 0,
  },
  infoLabel: { fontSize: 11, color: C.textSoft, letterSpacing: 0.3 },
  infoValue: { fontSize: 14, color: C.deep, fontWeight: 700, marginTop: 1 },

  actionRow: { display: "flex", gap: 10 },
  actionBtn: {
    flex: 1,
    padding: "13px",
    borderRadius: 12,
    border: "1px solid rgba(255,255,255,0.85)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.65), rgba(255,255,255,0.3))",
    color: C.deep,
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 13,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(11,59,46,0.06), inset 0 1px 0 rgba(255,255,255,0.9)",
    transition: "all 0.2s",
  },

  /* ----- RIGHT: history ----- */
  rightColumn: { position: "relative" },
  historyHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 22,
  },
  historyTitleRow: { display: "flex", alignItems: "center", gap: 12 },
  titleAccent: {
    width: 4, height: 30,
    borderRadius: 4,
    background: `linear-gradient(180deg,${C.forest},${C.mint})`,
    boxShadow: `0 0 18px ${C.mint}`,
  },
  historyTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 28,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.5,
  },
  countBadge: {
    padding: "7px 16px",
    borderRadius: 999,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.8)",
    color: C.forest,
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: 0.5,
    boxShadow: "0 2px 8px rgba(46,139,87,0.15)",
  },

  historyList: {
    display: "flex",
    flexDirection: "column",
    gap: 18,
  },
  loadingWrap: {
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    padding: "60px 0", gap: 16,
  },
  loadingSpinner: {
    width: 36, height: 36, borderRadius: "50%",
    border: `3px solid rgba(46,139,87,0.2)`,
    borderTopColor: C.emerald,
    animation: "spin 1s linear infinite",
  },
  loadingText: { fontSize: 14, color: C.textSoft, fontWeight: 600 },
  emptyWrap: {
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    padding: "60px 0", color: C.textSoft,
  },
  emptyText: { fontSize: 15, fontWeight: 600 },
  historyCardPending: {
    opacity: 0.75,
    border: `1px dashed rgba(46,139,87,0.4)`,
  },
  pendingBadge: {
    padding: "3px 10px", borderRadius: 999, fontSize: 11, fontWeight: 700,
    background: "rgba(46,139,87,0.12)", color: C.emerald,
    border: `1px solid rgba(46,139,87,0.25)`,
  },
  historyCard: {
    position: "relative",
    padding: "24px 26px",
    borderRadius: 22,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.4) 50%, rgba(200,242,220,0.3) 100%)",
    backdropFilter: "blur(28px) saturate(170%)",
    WebkitBackdropFilter: "blur(28px) saturate(170%)",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: [
      "0 18px 50px rgba(11,59,46,0.15)",
      "0 6px 18px rgba(11,59,46,0.06)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.1)",
    ].join(", "),
    overflow: "hidden",
    transition: "transform 0.2s",
  },
  historyTop: {
    display: "flex",
    gap: 24,
    alignItems: "flex-start",
  },
  historyTextSide: { flex: 1, minWidth: 0 },
  historyCardTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 18,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.3,
  },
  historyDate: {
    fontSize: 12,
    color: C.textSoft,
    margin: "8px 0 12px",
  },
  tagRow: { display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 },
  simBadge: {
    padding: "6px 14px",
    borderRadius: 999,
    background: `linear-gradient(135deg,${C.forest},${C.emerald})`,
    color: "#fff",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: 0.3,
    boxShadow: "0 4px 12px rgba(46,139,87,0.3)",
  },
  featureBadge: {
    padding: "6px 14px",
    borderRadius: 999,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.4))",
    border: "1px solid rgba(255,255,255,0.8)",
    color: C.forest,
    fontSize: 12,
    fontWeight: 600,
  },
  summary: {
    fontSize: 13,
    color: C.textSoft,
    lineHeight: 1.6,
    margin: 0,
  },

  thumbColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    flexShrink: 0,
  },
  thumbBox: {
    position: "relative",
    width: 130,
    height: 78,
    borderRadius: 12,
    overflow: "hidden",
    border: "1px solid rgba(255,255,255,0.85)",
    boxShadow: "0 6px 18px rgba(11,59,46,0.18), inset 0 1px 0 rgba(255,255,255,0.5)",
  },
  thumbImg: { width: "100%", height: "100%", objectFit: "cover", display: "block" },
  thumbLabel: {
    position: "absolute",
    top: 6, left: 6,
    width: 22, height: 22,
    borderRadius: 6,
    background: `linear-gradient(135deg,${C.deep},${C.emerald})`,
    color: "#fff",
    fontSize: 11,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
  },

  progressTrack: {
    height: 5,
    borderRadius: 999,
    background: "rgba(46,139,87,0.15)",
    overflow: "hidden",
    marginTop: 18,
  },
  progressFill: {
    height: "100%",
    background: `linear-gradient(90deg,${C.forest},${C.emerald},${C.mint})`,
    borderRadius: 999,
    boxShadow: `0 0 12px ${C.mint}`,
  },
  cardFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
  },
  footerLabel: { fontSize: 11, color: C.textSoft, letterSpacing: 0.3 },

  footerBtnGroup: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },

  deleteBtn: {
    padding: "8px 16px",
    borderRadius: 999,
    border: "1px solid rgba(180,60,60,0.25)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.65), rgba(255,230,230,0.45))",
    color: "#8A2D2D",
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 12,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(90,20,20,0.06), inset 0 1px 0 rgba(255,255,255,0.9)",
  },

  detailBtn: {
    padding: "8px 18px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.85)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.65), rgba(255,255,255,0.3))",
    color: C.forest,
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 12,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(11,59,46,0.06), inset 0 1px 0 rgba(255,255,255,0.9)",
  },

  accountModalCard: {
    position: "relative",
    width: "100%",
    maxWidth: 480,
    padding: "40px 44px 32px",
    borderRadius: 32,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.86) 0%, rgba(255,255,255,0.6) 50%, rgba(200,242,220,0.4) 100%)",
    backdropFilter: "blur(40px) saturate(200%)",
    WebkitBackdropFilter: "blur(40px) saturate(200%)",
    border: "1px solid rgba(255,255,255,0.85)",
    boxShadow: [
      "0 40px 100px rgba(11,59,46,0.3)",
      "0 12px 32px rgba(11,59,46,0.12)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.15)",
    ].join(", "),
    animation: "modalSlideUp 0.35s ease-out",
  },
  accountModalTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 24,
    fontWeight: 700,
    color: C.deep,
    margin: "0 0 8px",
  },
  accountModalDesc: {
    fontSize: 13,
    color: C.textSoft,
    lineHeight: 1.6,
    margin: "0 0 24px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    marginBottom: 16,
  },
  formLabel: {
    fontSize: 12,
    fontWeight: 800,
    color: C.forest,
    letterSpacing: 0.4,
  },
  formInput: {
    width: "100%",
    boxSizing: "border-box",
    padding: "13px 15px",
    borderRadius: 12,
    border: "1px solid rgba(46,139,87,0.22)",
    outline: "none",
    background: "rgba(255,255,255,0.68)",
    color: C.deep,
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 14,
    fontWeight: 700,
    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.9)",
  },
  formInputDisabled: {
    opacity: 0.75,
    cursor: "not-allowed",
    background: "rgba(200,242,220,0.35)",
  },
  accountCancelBtn: {
    padding: "14px 36px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.8)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.7), rgba(200,242,220,0.5))",
    color: C.forest,
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 4px 16px rgba(46,139,87,0.15), inset 0 1px 0 rgba(255,255,255,0.9)",
  },

  /* ===== Detail Modal ===== */
  modalOverlay: {
    position: "fixed",
    inset: 0,
    zIndex: 100,
    background: "rgba(11, 59, 46, 0.35)",
    backdropFilter: "blur(12px) saturate(120%)",
    WebkitBackdropFilter: "blur(12px) saturate(120%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 20px",
    animation: "modalFadeIn 0.3s ease-out",
  },
  modalCard: {
    position: "relative",
    width: "100%",
    maxWidth: 680,
    maxHeight: "85vh",
    overflowY: "auto",
    padding: "40px 44px 32px",
    borderRadius: 32,
    background:
      "linear-gradient(155deg, rgba(255,255,255,0.82) 0%, rgba(255,255,255,0.55) 50%, rgba(200,242,220,0.4) 100%)",
    backdropFilter: "blur(40px) saturate(200%)",
    WebkitBackdropFilter: "blur(40px) saturate(200%)",
    border: "1px solid rgba(255,255,255,0.85)",
    boxShadow: [
      "0 40px 100px rgba(11,59,46,0.3)",
      "0 12px 32px rgba(11,59,46,0.12)",
      "inset 0 1px 0 rgba(255,255,255,0.95)",
      "inset 0 -1px 0 rgba(46,139,87,0.15)",
    ].join(", "),
    animation: "modalSlideUp 0.35s ease-out",
  },
  modalClose: {
    position: "absolute",
    top: 18, right: 22,
    width: 36, height: 36,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.7)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.6), rgba(255,255,255,0.3))",
    color: C.textSoft,
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 8px rgba(11,59,46,0.06)",
    transition: "all 0.2s",
  },

  modalHeader: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 24,
  },
  modalTitleArea: { flex: 1, minWidth: 0 },
  modalBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 16px",
    borderRadius: 999,
    background: "linear-gradient(135deg, rgba(200,242,220,0.9), rgba(127,227,181,0.5))",
    border: "1px solid rgba(255,255,255,0.8)",
    color: C.forest,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 1,
    marginBottom: 14,
    boxShadow: "0 2px 8px rgba(46,139,87,0.15)",
  },
  modalBadgeDot: {
    width: 5, height: 5, borderRadius: "50%",
    background: `linear-gradient(135deg,${C.emerald},${C.mint})`,
    boxShadow: `0 0 8px ${C.mint}`,
  },
  modalTitle: {
    fontFamily: "'Chakra Petch',sans-serif",
    fontSize: 24,
    fontWeight: 700,
    color: C.deep,
    margin: 0,
    letterSpacing: -0.5,
    lineHeight: 1.3,
  },
  modalDate: { fontSize: 13, color: C.text, marginTop: 8 },
  modalDivider: {
    height: 1,
    margin: "24px 0",
    background: "linear-gradient(90deg, transparent, rgba(46,139,87,0.25), transparent)",
  },

  modalSection: { marginBottom: 24 },
  modalSectionLabel: {
    fontSize: 15,
    fontWeight: 800,
    color: C.deep,
    marginBottom: 12,
    fontFamily: "'Chakra Petch',sans-serif",
  },
  modalText: {
    fontSize: 14,
    color: C.text,
    lineHeight: 1.8,
    margin: 0,
  },

  modalSegmentList: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  modalSegment: {
    padding: "14px 18px",
    borderRadius: 14,
    background: "linear-gradient(155deg, rgba(255,255,255,0.6), rgba(200,242,220,0.3))",
    border: "1px solid rgba(255,255,255,0.8)",
    boxShadow: "0 4px 12px rgba(11,59,46,0.05), inset 0 1px 0 rgba(255,255,255,0.9)",
  },
  modalSegmentHeader: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 8,
  },
  modalSegmentBadge: {
    padding: "4px 12px",
    borderRadius: 999,
    background: `linear-gradient(135deg,${C.forest},${C.emerald})`,
    color: "#fff",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 0.3,
  },
  modalSegmentTime: {
    fontSize: 13,
    color: C.emerald,
    fontWeight: 700,
  },
  modalSegmentDesc: {
    fontSize: 13,
    color: C.text,
    lineHeight: 1.7,
    margin: 0,
  },

  modalDiffList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  modalDiffItem: {
    fontSize: 14,
    color: C.text,
    display: "flex",
    gap: 10,
    lineHeight: 1.7,
  },
  modalDiffBullet: {
    color: C.emerald,
    fontWeight: 700,
    flexShrink: 0,
  },

  modalFooter: {
    display: "flex",
    justifyContent: "center",
    gap: 14,
    marginTop: 28,
    paddingTop: 20,
    borderTop: "1px solid rgba(46,139,87,0.12)",
  },
  modalCloseBtn: {
    padding: "14px 48px",
    borderRadius: 999,
    border: "none",
    background: `linear-gradient(135deg,${C.deep} 0%,${C.forest} 40%,${C.emerald} 100%)`,
    color: "#fff",
    fontFamily: "'Rajdhani',sans-serif",
    fontSize: 15,
    fontWeight: 700,
    letterSpacing: 0.5,
    cursor: "pointer",
    boxShadow: `0 10px 28px rgba(46,139,87,0.4), inset 0 1px 0 rgba(255,255,255,0.3)`,
    transition: "transform 0.15s",
  },
  modalPdfBtn: {
  padding: "14px 36px",
  borderRadius: 999,
  border: "none",
  background: "linear-gradient(135deg, rgba(255,255,255,0.7), rgba(200,242,220,0.5))",
  color: C.forest,
  fontFamily: "'Rajdhani',sans-serif",
  fontSize: 15,
  fontWeight: 700,
  letterSpacing: 0.5,
  cursor: "pointer",
  boxShadow: "0 4px 16px rgba(46,139,87,0.15), inset 0 1px 0 rgba(255,255,255,0.9)",
  border: "1px solid rgba(255,255,255,0.8)",
  transition: "transform 0.15s",
  },
};