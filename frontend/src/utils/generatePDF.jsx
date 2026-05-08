/**
 * Tenein PDF Report Generator (v5 FINAL)
 * 위치: src/utils/generatePDF.jsx
 *
 * v5: fixed 제거 → 빈 페이지 해결, 표지 점수 텍스트로 변경
 */

import React from "react";
import {
  Document, Page, Text, View, Image,
  Font, StyleSheet, pdf,
} from "@react-pdf/renderer";

import coverBg from "../assets/pdf-cover-bg.png";
import bodyBg  from "../assets/pdf-body-bg.png";

/* ================================================================
   1. 폰트
   ================================================================ */
Font.register({
  family: "NotoSansKR",
  fonts: [
    { src: "/fonts/NotoSansKR-Regular.ttf", fontWeight: "normal" },
    { src: "/fonts/NotoSansKR-Bold.ttf",    fontWeight: "bold" },
  ],
});
Font.registerHyphenationCallback((word) => [word]);

/* ================================================================
   2. 색상
   ================================================================ */
const C = {
  deep: "#0B3B2E",
  forest: "#13513F",
  emerald: "#2E8B57",
  mint: "#7FE3B5",
  text: "#0E2A20",
  textSoft: "#3B5A4B",
  white: "#FFFFFF",
  divider: "#C8F2DC",
};

/* ================================================================
   3. 스타일
   ================================================================ */
const s = StyleSheet.create({
  /* ---- 배경 이미지 ---- */
  bgWrap: { height: 0, overflow: "visible" },
  pageBgImg: {
    position: "absolute", top: 0, left: 0,
    width: 595, height: 842,
  },

  /* ---- 표지 ---- */
  coverPage: { fontFamily: "NotoSansKR" },
  coverContent: {
    flex: 1,
    paddingTop: 140,
    paddingBottom: 320,
    paddingHorizontal: 70,
    alignItems: "center",
    justifyContent: "center",
  },
  coverLabel: {
    fontSize: 11, color: C.emerald,
    letterSpacing: 3, marginBottom: 14, fontWeight: "bold",
  },
  coverTitle: {
    fontSize: 26, fontWeight: "bold",
    color: C.deep, textAlign: "center", marginBottom: 6,
  },
  coverSubtitle: {
    fontSize: 13, color: C.textSoft,
    textAlign: "center", marginBottom: 36,
  },
  coverDivider: {
    width: 60, height: 2,
    backgroundColor: C.mint, marginBottom: 36,
  },
  coverInfoRow: {
    flexDirection: "row", marginBottom: 8, alignItems: "center",
  },
  coverInfoLabel: {
    fontSize: 10, color: C.textSoft, width: 70,
    textAlign: "right", marginRight: 10,
  },
  coverInfoValue: { fontSize: 10, color: C.deep, fontWeight: "bold" },
  coverScoreWrap: { marginTop: 32, alignItems: "center" },
  coverScoreNum: { fontSize: 40, fontWeight: "bold", color: C.deep },
  coverScoreLabel: { fontSize: 12, color: C.emerald, marginTop: 2 },

  /* ---- 본문 ---- */
  bodyPage: { fontFamily: "NotoSansKR" },
  bodyContent: {
    // flex: 1,
    paddingTop: 55,
    paddingBottom: 60,
    paddingHorizontal: 65,
  },

  /* ---- 섹션 ---- */
  sectionTitle: {
    fontSize: 15, fontWeight: "bold", color: C.deep,
    marginBottom: 14, paddingBottom: 6,
    borderBottomWidth: 1.5, borderBottomColor: C.divider,
  },
  bodyText: {
    fontSize: 10, color: C.text, lineHeight: 1.8, marginBottom: 16,
  },

  /* ---- 차이점 ---- */
  diffItem: { flexDirection: "row", marginBottom: 6, paddingLeft: 4 },
  diffBullet: {
    fontSize: 10, color: C.emerald, fontWeight: "bold",
    marginRight: 8, width: 10,
  },
  diffText: { fontSize: 10, color: C.text, lineHeight: 1.7, flex: 1 },

  /* ---- 구간 카드 ---- */
  segCard: {
    marginBottom: 18, padding: 14,
    borderWidth: 1, borderColor: C.divider, borderRadius: 8,
  },
  segHeader: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center", marginBottom: 8,
  },
  segBadge: {
    fontSize: 10, fontWeight: "bold", color: C.white,
    backgroundColor: C.forest,
    paddingVertical: 3, paddingHorizontal: 10, borderRadius: 10,
  },
  segScore: { fontSize: 10, fontWeight: "bold", color: C.emerald },
  segTimeRow: {
    flexDirection: "row", justifyContent: "space-between", marginBottom: 10,
  },
  segTimeLabel: { fontSize: 9, color: C.textSoft },
  segTimeValue: { fontSize: 9, color: C.deep, fontWeight: "bold" },
  segScreenshotRow: { flexDirection: "row", marginBottom: 10 },
  segScreenshotWrap: {
    flex: 1, height: 95, overflow: "hidden",
    borderWidth: 0.5, borderColor: C.divider, borderRadius: 4,
    marginHorizontal: 4,
  },
  segScreenshot: { width: "100%", height: "100%", objectFit: "cover" },
  segScreenshotPlaceholder: {
    width: "100%", height: "100%", backgroundColor: "#F0F0F0",
    alignItems: "center", justifyContent: "center",
  },
  segScreenshotLabel: {
    fontSize: 8, fontWeight: "bold", color: C.white,
    backgroundColor: C.forest,
    paddingVertical: 1, paddingHorizontal: 5, borderRadius: 3,
    marginBottom: 4,
  },
  segDesc: { fontSize: 9.5, color: C.text, lineHeight: 1.7 },

  /* ---- 푸터 ---- */
  footerPage: { fontFamily: "NotoSansKR" },
  footerContent: {
    flex: 1,
    paddingTop: 140, paddingBottom: 340, paddingHorizontal: 80,
    alignItems: "center", justifyContent: "center",
  },
  footerNotice: {
    fontSize: 11, color: C.textSoft,
    textAlign: "center", lineHeight: 1.8, marginBottom: 20,
  },
  footerDivider: {
    width: 200, height: 1,
    backgroundColor: C.divider, marginVertical: 20,
  },
  footerMeta: { fontSize: 9, color: C.textSoft, textAlign: "center", marginBottom: 4 },
  footerDisclaimer: {
    fontSize: 9, color: C.textSoft,
    textAlign: "center", lineHeight: 1.7,
    marginTop: 20, marginBottom: 30,
  },
  footerBrand: {
    fontSize: 18, fontWeight: "bold",
    color: C.deep, textAlign: "center", marginBottom: 4,
  },
  footerBrandSub: {
    fontSize: 10, color: C.emerald, textAlign: "center", marginBottom: 6,
  },
  footerCopyright: { fontSize: 8, color: C.textSoft, textAlign: "center" },
});

/* ================================================================
   4. 영상 프레임 순차 캡처
   ================================================================ */
function captureFramesFromVideo(videoUrl, times) {
  return new Promise((resolve) => {
    if (!videoUrl || times.length === 0) return resolve([]);
    const results = new Array(times.length).fill(null);
    const video = document.createElement("video");
    video.crossOrigin = "anonymous";
    video.muted = true;
    video.preload = "auto";
    video.src = videoUrl;
    let idx = 0;
    const timeout = setTimeout(() => { video.src = ""; resolve(results); }, 15000);
    const captureNext = () => {
      if (idx >= times.length) { clearTimeout(timeout); video.src = ""; resolve(results); return; }
      video.currentTime = Math.min(times[idx], video.duration - 0.1);
    };
    video.addEventListener("loadeddata", () => captureNext());
    video.addEventListener("seeked", () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = Math.min(video.videoWidth, 640);
        canvas.height = Math.min(video.videoHeight, 360);
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        results[idx] = canvas.toDataURL("image/jpeg", 0.75);
      } catch { results[idx] = null; }
      idx++;
      captureNext();
    });
    video.addEventListener("error", () => { clearTimeout(timeout); resolve(results); });
  });
}

async function captureAllScreenshots(data) {
  const shots = {};
  if (!data.segments?.length) return shots;
  const timesA = [], timesB = [];
  for (const seg of data.segments) {
    timesA.push(seg.startA != null ? (seg.startA + seg.endA) / 2 : 1);
    timesB.push(seg.startB != null ? (seg.startB + seg.endB) / 2 : 1);
  }
  const framesA = data.videoUrlA ? await captureFramesFromVideo(data.videoUrlA, timesA) : [];
  const framesB = data.videoUrlB ? await captureFramesFromVideo(data.videoUrlB, timesB) : [];
  data.segments.forEach((seg, i) => {
    shots[`${seg.id}_a`] = framesA[i] || null;
    shots[`${seg.id}_b`] = framesB[i] || null;
  });
  return shots;
}

/* ================================================================
   5. 시간 헬퍼
   ================================================================ */
function fmtTime(sec) {
  if (sec == null) return "--:--";
  return `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;
}
function fmtTimeRange(start, end) { return `${fmtTime(start)} - ${fmtTime(end)}`; }
function parseTimeStr(timeStr) {
  if (!timeStr) return null;
  const match = timeStr.match(/(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})/);
  if (!match) return null;
  return {
    start: parseInt(match[1]) * 60 + parseInt(match[2]),
    end: parseInt(match[3]) * 60 + parseInt(match[4]),
  };
}
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}
function nowStr() {
  const d = new Date();
  return `${todayStr()} ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}:${String(d.getSeconds()).padStart(2,"0")}`;
}

/* ================================================================
   6. PDF 페이지 컴포넌트
   ================================================================ */

const CoverPage = ({ data }) => (
  <Page size="A4" style={s.coverPage}>
    <View style={s.bgWrap}>
      <Image src={coverBg} style={s.pageBgImg} />
    </View>
    <View style={s.coverContent}>
      <Text style={s.coverLabel}>CHOREOGRAPHY  ANALYSIS  REPORT</Text>
      <Text style={s.coverTitle}>안무 유사도 분석 보고서</Text>
      <Text style={s.coverSubtitle}>K-pop Visual Studio</Text>
      <View style={s.coverDivider} />
      <View style={s.coverInfoRow}>
        <Text style={s.coverInfoLabel}>영상 A :</Text>
        <Text style={s.coverInfoValue}>{data.titleA || "Video A"}</Text>
      </View>
      <View style={s.coverInfoRow}>
        <Text style={s.coverInfoLabel}>영상 B :</Text>
        <Text style={s.coverInfoValue}>{data.titleB || "Video B"}</Text>
      </View>
      <View style={s.coverInfoRow}>
        <Text style={s.coverInfoLabel}>분석일 :</Text>
        <Text style={s.coverInfoValue}>{data.date || todayStr()}</Text>
      </View>
      {data.analysisId && (
        <View style={s.coverInfoRow}>
          <Text style={s.coverInfoLabel}>분석 ID :</Text>
          <Text style={s.coverInfoValue}>#{data.analysisId}</Text>
        </View>
      )}
      <View style={s.coverScoreWrap}>
        <Text style={s.coverScoreNum}>{data.score ?? 0}%</Text>
        <Text style={s.coverScoreLabel}>전체 유사도</Text>
      </View>
    </View>
  </Page>
);

const SummaryPage = ({ data }) => (
  <Page size="A4" style={s.bodyPage} wrap>
    <View style={s.bgWrap}>
      <Image src={bodyBg} style={s.pageBgImg} />
    </View>
    <View style={s.bodyContent}>
      <Text style={s.sectionTitle}>분석 개요</Text>
      <Text style={s.bodyText}>
        {data.interpretation || data.summary || "분석 개요가 없습니다."}
      </Text>
      {data.summary && data.interpretation && (
        <View wrap={false}>
          <Text style={s.sectionTitle}>요약</Text>
          <Text style={s.bodyText}>{data.summary}</Text>
        </View>
      )}
      {data.keyDifferences?.length > 0 && (
        <View wrap={false}>
          <Text style={s.sectionTitle}>주요 차이점</Text>
          {data.keyDifferences.map((diff, i) => (
            <View key={i} style={s.diffItem}>
              <Text style={s.diffBullet}>•</Text>
              <Text style={s.diffText}>{diff}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  </Page>
);

const SegmentCard = ({ seg, screenshots }) => {
  const shotA = screenshots?.[`${seg.id}_a`];
  const shotB = screenshots?.[`${seg.id}_b`];
  return (
    <View style={s.segCard} wrap={false}>
      <View style={s.segHeader}>
        <Text style={s.segBadge}>구간 {seg.id}</Text>
        {seg.score != null && <Text style={s.segScore}>유사도 {seg.score}%</Text>}
      </View>
      <View style={s.segTimeRow}>
        <View>
          <Text style={s.segTimeLabel}>영상 A</Text>
          <Text style={s.segTimeValue}>{seg.timeA}</Text>
        </View>
        <View>
          <Text style={s.segTimeLabel}>영상 B</Text>
          <Text style={s.segTimeValue}>{seg.timeB}</Text>
        </View>
      </View>
      {(shotA || shotB) && (
        <View style={s.segScreenshotRow}>
          <View style={s.segScreenshotWrap}>
            {shotA ? <Image src={shotA} style={s.segScreenshot} /> : (
              <View style={s.segScreenshotPlaceholder}>
                <Text style={s.segScreenshotLabel}>A</Text>
              </View>
            )}
          </View>
          <View style={s.segScreenshotWrap}>
            {shotB ? <Image src={shotB} style={s.segScreenshot} /> : (
              <View style={s.segScreenshotPlaceholder}>
                <Text style={s.segScreenshotLabel}>B</Text>
              </View>
            )}
          </View>
        </View>
      )}
      <Text style={s.segDesc}>{seg.description}</Text>
    </View>
  );
};

const SegmentsPage = ({ data, screenshots }) => (
  <>
    {(data.segments || []).map((seg, i) => (
      <Page key={seg.id} size="A4" style={s.bodyPage}>
        <View style={s.bgWrap}>
          <Image src={bodyBg} style={s.pageBgImg} />
        </View>
        <View style={s.bodyContent}>
          {i === 0 && (
            <Text style={s.sectionTitle}>
              유사 구간 분석 ({data.segments.length}개)
            </Text>
          )}
          <SegmentCard seg={seg} screenshots={screenshots} />
        </View>
      </Page>
    ))}
  </>
);

const FooterPage = ({ data }) => (
  <Page size="A4" style={s.footerPage}>
    <View style={s.bgWrap}>
      <Image src={bodyBg} style={s.pageBgImg} />
    </View>
    <View style={s.footerContent}>
      <Text style={s.footerNotice}>
        본 보고서는 Tenein AI 시스템에 의해{"\n"}자동 생성되었습니다.
      </Text>
      <Text style={s.footerMeta}>분석 모델: Tenein AI</Text>
      <Text style={s.footerMeta}>분석 시각: {data.analyzedAt || nowStr()}</Text>
      {data.elapsed && <Text style={s.footerMeta}>처리 시간: {data.elapsed}초</Text>}
      <View style={s.footerDivider} />
      <Text style={s.footerDisclaimer}>
        이 보고서의 분석 결과는 AI 모델의 판단이며,{"\n"}
        법적 효력이 없습니다.{"\n"}
        안무 저작권 관련 판단은 전문가의 자문을 권장합니다.
      </Text>
      <Text style={s.footerBrand}>Tenein</Text>
      <Text style={s.footerBrandSub}>K-pop Visual Studio</Text>
      <Text style={s.footerCopyright}>© 2026 Kookmin Univ Captstone Tenein Team</Text>
    </View>
  </Page>
);

/* ================================================================
   7. 전체 PDF 문서
   ================================================================ */
const TeneinReport = ({ data, screenshots }) => (
  <Document
    title={`Tenein 분석보고서 - ${data.date || todayStr()}`}
    author="Tenein AI"
    subject="안무 유사도 분석 보고서"
  >
    <CoverPage data={data} />
    <SummaryPage data={data} />
    {data.segments?.length > 0 && (
      <SegmentsPage data={data} screenshots={screenshots} />
    )}
    <FooterPage data={data} />
  </Document>
);

/* ================================================================
   8. 데이터 정규화
   ================================================================ */
function normalizeData(raw) {
  if (raw.overall) {
    return {
      score: raw.overall.score ?? 0,
      interpretation: raw.overall.interpretation || "",
      summary: raw.summary || "",
      keyDifferences: raw.key_differences || [],
      segments: (raw.segments || []).map((seg) => {
        const pA = parseTimeStr(seg.timeA);
        const pB = parseTimeStr(seg.timeB);
        console.log(pA)
        console.log(pB)
        return {
          id: seg.id, score: seg.score ?? null,
          timeA: seg.timeA || "", timeB: seg.timeB || "",
          startA: pA?.start ?? null, endA: pA?.end ?? null,
          startB: pB?.start ?? null, endB: pB?.end ?? null,
          description: seg.desc || seg.description || "",
        };
      }),
      titleA: raw.titleA || "Video A",
      titleB: raw.titleB || "Video B",
      videoUrlA: raw.videoUrlA || null,
      videoUrlB: raw.videoUrlB || null,
      date: raw.date || todayStr(),
      analysisId: raw.analysisId || raw.video_a_id || null,
      analyzedAt: raw.analyzedAt || nowStr(),
      elapsed: raw.elapsed || null,
    };
  }
  return {
    score: raw.similarity ?? 0,
    interpretation: raw.interpretation || "",
    summary: raw.summary || "",
    keyDifferences: raw.keyDifferences || [],
    segments: (raw.segments || []).map((seg) => {
      const pA = parseTimeStr(seg.timeA);
      const pB = parseTimeStr(seg.timeB);
      return {
        id: seg.id, score: seg.score ?? null,
        timeA: seg.timeA || "", timeB: seg.timeB || "",
        startA: pA?.start ?? null, endA: pA?.end ?? null,
        startB: pB?.start ?? null, endB: pB?.end ?? null,
        description: seg.desc || seg.description || "",
      };
    }),
    titleA: raw.titleA || "Video A",
    titleB: raw.titleB || "Video B",
    videoUrlA: raw.thumbA || null,
    videoUrlB: raw.thumbB || null,
    date: raw.date || todayStr(),
    analysisId: raw.id || null,
    analyzedAt: raw.analyzedAt || nowStr(),
    elapsed: raw.elapsed || null,
  };
}

/* ================================================================
   9. 메인 내보내기
   ================================================================ */
export async function generatePDF(rawData) {
  
  const data = normalizeData(rawData);
  console.log("2a. startA 확인:", data.segments[0].startA, data.segments[0].endA);  // ⭐ 여기
  let screenshots = {};
  try {
    screenshots = await captureAllScreenshots(data);
  } catch (err) {
    console.warn("스크린샷 캡처 실패:", err);
  }
  const doc = <TeneinReport data={data} screenshots={screenshots} />;
  const blob = await pdf(doc).toBlob();
  const fileName = `Tenein_분석보고서_${data.date || todayStr()}.pdf`;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}