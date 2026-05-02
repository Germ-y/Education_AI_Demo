import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(backendDir, "..");
const outputDir = path.join(repoRoot, "examples", "generated", "fraction-mission");
const imagePath = path.join(outputDir, "fraction-pizza.png");
const jsonPath = path.join(outputDir, "sample-content.json");
const htmlPath = path.join(outputDir, "index.html");

async function loadEnv() {
  const envPaths = [path.join(backendDir, ".env"), path.join(repoRoot, ".env")];
  for (const envPath of envPaths) {
    try {
      const envText = await fs.readFile(envPath, "utf8");
      for (const line of envText.split(/\r?\n/)) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;
        const index = trimmed.indexOf("=");
        if (index === -1) continue;
        const key = trimmed.slice(0, index).trim();
        const value = trimmed.slice(index + 1).trim().replace(/^['"]|['"]$/g, "");
        if (!process.env[key]) process.env[key] = value;
      }
      return;
    } catch {
      // Try the next supported env location.
    }
  }
}

function getImagePrompt() {
  return [
    "Create a premium Korean edtech mission-card illustration for a middle school student learning fractions.",
    "Visual concept: a round pizza becomes a small top-down adventure map on a clean study desk, like a friendly math quest board.",
    "The pizza must be divided by clear cross-shaped gaps into exactly four equal quarter regions.",
    "Exactly one quarter region is lifted slightly and glowing with warm golden light, while the other three equal regions stay visible and calm.",
    "Add subtle mission-scene details around the pizza: a tiny compass token, four small round counters near the plate with exactly one counter glowing, soft paper-cut or clay-like 3D texture, gentle shadows.",
    "Make it feel imaginative and useful for explaining 'one out of four equal parts', not like a plain food illustration.",
    "Use cheerful but not childish colors, clean composition, enough empty margin for UI overlay, no clutter.",
    "Do not include any text, letters, numbers, labels, watermark, logo, or speech bubbles anywhere in the image.",
  ].join(" ");
}

async function callImageApi(model, prompt, apiKey) {
  const response = await fetch("https://api.openai.com/v1/images/generations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      prompt,
      size: "1024x1024",
      quality: "high",
      output_format: "png",
      n: 1,
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    const message = payload?.error?.message || `Image API request failed with ${response.status}`;
    throw new Error(message);
  }

  const item = payload?.data?.[0];
  if (item?.b64_json) return Buffer.from(item.b64_json, "base64");
  if (item?.url) {
    const imageResponse = await fetch(item.url);
    if (!imageResponse.ok) {
      throw new Error(`Failed to download generated image: ${imageResponse.status}`);
    }
    return Buffer.from(await imageResponse.arrayBuffer());
  }

  throw new Error("Image API response did not include b64_json or url.");
}

async function generateImage() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is missing. Add it to .env before running this script.");
  }

  const imageModel = process.env.OPENAI_IMAGE_MODEL || "gpt-image-2";
  const prompt = getImagePrompt();
  const imageBuffer = await callImageApi(imageModel, prompt, apiKey);
  return { imageBuffer, imageModel, imagePrompt: prompt };
}

function buildContent({ imageModel, imagePrompt }) {
  return {
    id: "content_fraction_001",
    title: "분수 탐험: 빛나는 한 조각",
    status: "teacher_review",
    generatedAt: new Date().toISOString(),
    generation: {
      imageModel,
      promptVersion: "creative-mission-card-v2",
      imagePrompt,
    },
    student: {
      id: "stu_sumin",
      displayName: "수민",
      grade: "중학교 2학년",
    },
    orchestratorDecision: {
      sessionGoal: "전체와 부분의 관계를 그림으로 이해하고 1/4을 말할 수 있다.",
      diagnosis: ["개념 미이해", "분모/분자 역할 혼동", "자신감 저하"],
      strategy: "첫 문항은 정답 가능성이 높은 쉬운 성공 경험으로 시작하고, 탐험 지도처럼 보이는 피자 이미지를 통해 전체 조각 수와 선택한 조각 수를 분리해서 설명한다.",
      teacherNote: "이미지를 먼저 보여주고, '전체 구역은 몇 개?', '빛나는 구역은 몇 개?' 순서로 질문하세요.",
    },
    assets: [
      {
        id: "img_fraction_pizza_001",
        type: "image",
        purpose: "concept_anchor",
        path: "fraction-pizza.png",
        alt: "4개의 같은 구역으로 나뉜 피자 지도에서 한 구역이 빛나는 그림",
      },
    ],
    blocks: [
      {
        id: "block_intro",
        type: "mission_intro",
        order: 1,
        studentText: "오늘은 빛나는 한 조각을 찾아보면서 1/4을 알아볼 거예요.",
      },
      {
        id: "block_image",
        type: "image_anchor",
        order: 2,
        imageAssetId: "img_fraction_pizza_001",
        studentText: "피자 지도가 똑같이 4구역으로 나뉘어 있어요. 빛나는 구역은 그중 1구역이에요.",
      },
      {
        id: "block_explain",
        type: "micro_explanation",
        order: 3,
        studentText: "아래 숫자 4는 전체 조각 수예요. 위 숫자 1은 내가 고른 조각 수예요.",
      },
      {
        id: "block_quiz",
        type: "choice_question",
        order: 4,
        question: "4구역 중 빛나는 1구역은 몇 분의 몇일까요?",
        choices: [
          { id: "a", text: "1/4" },
          { id: "b", text: "4/1" },
          { id: "c", text: "1/2" },
        ],
        answer: "a",
      },
      {
        id: "block_feedback",
        type: "adaptive_feedback",
        order: 5,
        feedback: {
          correct: "좋아요. 전체 4구역 중 1구역이니까 1/4이에요.",
          wrong: "괜찮아요. 아래 숫자는 전체 구역 수, 위 숫자는 빛나는 구역 수예요. 다시 그림을 보면서 세어볼까요?",
        },
      },
      {
        id: "block_repair",
        type: "repair_card",
        order: 6,
        studentText: "헷갈릴 땐 이렇게 생각해요. 전체가 몇 개인지 먼저 세고, 내가 가진 것이 몇 개인지 나중에 세요.",
      },
      {
        id: "block_reflection",
        type: "reflection",
        order: 7,
        question: "오늘 내용은 어땠나요?",
        choices: ["쉬웠어요", "조금 헷갈렸어요", "다시 보고 싶어요"],
      },
      {
        id: "block_next",
        type: "next_action",
        order: 8,
        studentText: "다음 미션에서는 2조각을 고르면 2/4가 되는지 알아볼 거예요.",
      },
    ],
    teacherApproval: {
      required: true,
      status: "pending",
      checklist: ["이미지 개념 일치", "문항 정답 확인", "문장 길이 적절", "학생에게 민감 정보 미노출"],
    },
  };
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildHtml(content) {
  const quiz = content.blocks.find((block) => block.type === "choice_question");
  const imageBlock = content.blocks.find((block) => block.type === "image_anchor");
  const explanation = content.blocks.find((block) => block.type === "micro_explanation");
  const intro = content.blocks.find((block) => block.type === "mission_intro");
  const feedback = content.blocks.find((block) => block.type === "adaptive_feedback");
  const repair = content.blocks.find((block) => block.type === "repair_card");
  const reflection = content.blocks.find((block) => block.type === "reflection");
  const next = content.blocks.find((block) => block.type === "next_action");

  const choiceButtons = quiz.choices
    .map((choice) => `<button class="choice" type="button">${escapeHtml(choice.text)}</button>`)
    .join("\n              ");

  const reflectionButtons = reflection.choices
    .map((choice) => `<button class="pill" type="button">${escapeHtml(choice)}</button>`)
    .join("\n              ");

  return `<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(content.title)}</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #172033;
        --muted: #697386;
        --line: #d9e1ec;
        --blue: #2f6fed;
        --green: #20835a;
        --yellow: #fff3c4;
        --bg: #f5f7fb;
        --panel: #ffffff;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: Inter, Apple SD Gothic Neo, Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background: var(--bg);
      }

      main {
        min-height: 100vh;
        display: grid;
        grid-template-columns: minmax(320px, 1fr) 380px;
        gap: 24px;
        padding: 28px;
      }

      .student-screen,
      .teacher-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 12px 34px rgba(35, 46, 75, 0.08);
      }

      .student-screen {
        overflow: hidden;
      }

      .mission-top {
        padding: 28px 32px 18px;
        border-bottom: 1px solid var(--line);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .eyebrow {
        margin: 0 0 8px;
        color: var(--blue);
        font-size: 14px;
        font-weight: 700;
      }

      h1,
      h2,
      h3,
      p {
        margin-top: 0;
      }

      h1 {
        margin-bottom: 0;
        font-size: 30px;
        line-height: 1.2;
        letter-spacing: 0;
      }

      .progress {
        min-width: 104px;
        height: 12px;
        border-radius: 999px;
        background: #e9eef7;
        overflow: hidden;
      }

      .progress span {
        display: block;
        width: 62%;
        height: 100%;
        background: var(--green);
      }

      .mission-body {
        display: grid;
        grid-template-columns: minmax(280px, 0.9fr) minmax(320px, 1.1fr);
        gap: 28px;
        padding: 32px;
      }

      .image-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #fbfcff;
      }

      .image-card img {
        display: block;
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: cover;
      }

      .image-card p {
        margin: 0;
        padding: 18px;
        color: var(--muted);
        font-size: 17px;
        line-height: 1.55;
      }

      .play-stack {
        display: grid;
        gap: 18px;
        align-content: start;
      }

      .card {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 20px;
        background: #fff;
      }

      .card.highlight {
        border-color: #f0cf62;
        background: var(--yellow);
      }

      .card h2 {
        margin-bottom: 10px;
        font-size: 22px;
        letter-spacing: 0;
      }

      .card p {
        margin-bottom: 0;
        color: var(--muted);
        font-size: 17px;
        line-height: 1.55;
      }

      .choices,
      .pills {
        display: grid;
        gap: 10px;
      }

      .choice,
      .pill,
      .approve {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        color: var(--ink);
        min-height: 48px;
        padding: 0 16px;
        font: inherit;
        font-weight: 700;
        cursor: default;
      }

      .choice:first-child {
        border-color: rgba(32, 131, 90, 0.45);
        background: #eaf8f1;
        color: #0d6844;
      }

      .pills {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .pill {
        min-height: 40px;
        font-size: 14px;
      }

      .teacher-panel {
        padding: 24px;
        align-self: start;
      }

      .teacher-panel h2 {
        font-size: 22px;
        margin-bottom: 16px;
      }

      .meta-list {
        display: grid;
        gap: 12px;
        margin: 0 0 20px;
      }

      .meta {
        border-left: 3px solid var(--blue);
        padding-left: 12px;
      }

      .meta strong {
        display: block;
        margin-bottom: 4px;
        font-size: 14px;
      }

      .meta span {
        display: block;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.5;
      }

      .checklist {
        padding: 16px;
        border-radius: 8px;
        background: #f6f8fc;
      }

      .checklist p {
        margin-bottom: 10px;
        font-weight: 700;
      }

      .checklist ul {
        margin: 0;
        padding-left: 20px;
        color: var(--muted);
        line-height: 1.8;
      }

      .approve {
        width: 100%;
        margin-top: 18px;
        border-color: var(--blue);
        background: var(--blue);
        color: #fff;
      }

      @media (max-width: 960px) {
        main,
        .mission-body {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="student-screen" aria-label="학생 미션 화면">
        <div class="mission-top">
          <div>
            <p class="eyebrow">오늘의 미션</p>
            <h1>${escapeHtml(content.title)}</h1>
          </div>
          <div class="progress" aria-label="진행률"><span></span></div>
        </div>

        <div class="mission-body">
          <figure class="image-card">
            <img src="./fraction-pizza.png" alt="${escapeHtml(content.assets[0].alt)}" />
            <p>${escapeHtml(imageBlock.studentText)}</p>
          </figure>

          <div class="play-stack">
            <section class="card highlight">
              <h2>${escapeHtml(intro.studentText)}</h2>
              <p>${escapeHtml(explanation.studentText)}</p>
            </section>

            <section class="card">
              <h2>${escapeHtml(quiz.question)}</h2>
              <div class="choices">
                ${choiceButtons}
              </div>
            </section>

            <section class="card">
              <h2>맞으면</h2>
              <p>${escapeHtml(feedback.feedback.correct)}</p>
            </section>

            <section class="card">
              <h2>헷갈리면</h2>
              <p>${escapeHtml(repair.studentText)}</p>
            </section>

            <section class="card">
              <h2>${escapeHtml(reflection.question)}</h2>
              <div class="pills">
                ${reflectionButtons}
              </div>
            </section>

            <section class="card">
              <h2>다음 미션</h2>
              <p>${escapeHtml(next.studentText)}</p>
            </section>
          </div>
        </div>
      </section>

      <aside class="teacher-panel" aria-label="교사 검토 패널">
        <p class="eyebrow">교사 승인 대기</p>
        <h2>AI 생성 콘텐츠 검토</h2>
        <div class="meta-list">
          <div class="meta">
            <strong>회기 목표</strong>
            <span>${escapeHtml(content.orchestratorDecision.sessionGoal)}</span>
          </div>
          <div class="meta">
            <strong>진단</strong>
            <span>${escapeHtml(content.orchestratorDecision.diagnosis.join(", "))}</span>
          </div>
          <div class="meta">
            <strong>전략</strong>
            <span>${escapeHtml(content.orchestratorDecision.strategy)}</span>
          </div>
          <div class="meta">
            <strong>사용 이미지 모델</strong>
            <span>${escapeHtml(content.generation.imageModel)}</span>
          </div>
        </div>
        <div class="checklist">
          <p>승인 전 확인</p>
          <ul>
            ${content.teacherApproval.checklist.map((item) => `<li>${escapeHtml(item)}</li>`).join("\n            ")}
          </ul>
        </div>
        <button class="approve" type="button">승인하고 학생에게 배포</button>
      </aside>
    </main>
  </body>
</html>`;
}

async function main() {
  await loadEnv();
  await fs.mkdir(outputDir, { recursive: true });

  const generation = await generateImage();
  await fs.writeFile(imagePath, generation.imageBuffer);

  const content = buildContent(generation);
  await fs.writeFile(jsonPath, `${JSON.stringify(content, null, 2)}\n`, "utf8");
  await fs.writeFile(htmlPath, buildHtml(content), "utf8");

  return {
    imageModel: generation.imageModel,
    imagePath,
    jsonPath,
    htmlPath,
  };
}

main()
  .then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  })
  .catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
  });
