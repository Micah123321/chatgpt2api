const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const ts = require("typescript");

const stub = (tag) => ({ children, ...props }) => React.createElement(tag, props, children);
const load = (name) => {
  if (name === "@/components/ui/button") {
    return { Button: stub("button") };
  }
  if (name === "@/lib/utils") {
    return { cn: (...values) => values.filter(Boolean).join(" ") };
  }
  if (name === "@/components/image-lightbox") return { ImageLightbox: () => null };
  if (name === "@/components/ui/input") return { Input: stub("input") };
  if (name === "@/components/ui/textarea") return { Textarea: stub("textarea") };
  if (name === "@/components/ui/select") {
    return Object.fromEntries(
      ["Select", "SelectContent", "SelectItem", "SelectTrigger", "SelectValue"].map((component) => [component, stub("div")]),
    );
  }
  return require(name);
};
function loadComponent(file, exportName) {
  const source = fs.readFileSync(path.join(__dirname, file), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const componentModule = { exports: {} };
  new Function("require", "module", "exports", compiled)(load, componentModule, componentModule.exports);
  return componentModule.exports[exportName];
}
const ImageResults = loadComponent("../src/app/image/components/image-results.tsx", "ImageResults");
const ImageComposer = loadComponent("../src/app/image/components/image-composer.tsx", "ImageComposer");

function renderTurn(maskImages) {
  const turn = {
    id: "turn-1", prompt: "修改标注区域", model: "gpt-image-2", mode: "edit",
    referenceImages: [{ name: "source.png", dataUrl: "data:image/png;base64,c291cmNl", type: "image/png" }],
    maskImages, count: 1, size: "1024x1024", ratio: "1:1", tier: "1k", quality: "auto",
    images: [], createdAt: "2026-09-20T00:00:00Z", status: "queued",
  };
  const conversation = {
    id: "conversation-1", title: "编辑", model: turn.model, turns: [turn],
    createdAt: turn.createdAt, updatedAt: turn.createdAt,
  };
  const noop = () => {};
  return renderToStaticMarkup(React.createElement(ImageResults, {
    selectedConversation: conversation,
    onOpenLightbox: noop, onContinueEdit: noop, onAnnotateImage: noop,
    onDeletePrompt: noop, onDeleteResults: noop, onReuseTurnConfig: noop,
    onRegenerateTurn: noop, onRetryImage: noop, onTimeoutRetryContinue: noop,
    onDismissErrors: noop, formatConversationTime: () => "刚刚",
  }));
}

test("annotated edit displays both source and the submitted mask in this turn", () => {
  const markup = renderTurn([{ name: "edit-mask.png", dataUrl: "data:image/png;base64,bWFzaw==", type: "image/png" }]);
  assert.match(markup, /data:image\/png;base64,c291cmNl/);
  assert.match(markup, /data:image\/png;base64,bWFzaw==/);
  assert.match(markup, /标注遮罩/);
});

test("ordinary reference-only edit does not show mask label", () => {
  const markup = renderTurn([]);
  assert.doesNotMatch(markup, /标注遮罩/);
});

test("composer shows the pending mask alongside the source before submission", () => {
  const noop = () => {};
  const markup = renderToStaticMarkup(React.createElement(ImageComposer, {
    prompt: "修改标注区域", imageCount: "1", imageRatio: "1:1", imageTier: "1k",
    imageWidth: "1024", imageHeight: "1024", imageQuality: "auto", imageModel: "gpt-image-2",
    imageModels: ["gpt-image-2"], availableQuota: "", activeTaskCount: 0,
    referenceImages: [{ name: "source.png", dataUrl: "data:image/png;base64,c291cmNl" }],
    maskImages: [{ name: "edit-mask.png", dataUrl: "data:image/png;base64,bWFzaw==" }],
    textareaRef: { current: null }, fileInputRef: { current: null },
    onPromptChange: noop, onImageCountChange: noop, onImageRatioChange: noop,
    onImageTierChange: noop, onImageWidthChange: noop, onImageHeightChange: noop,
    onImageQualityChange: noop, onImageModelChange: noop, onSubmit: noop,
    onPickReferenceImage: noop, onReferenceImageChange: noop, onRemoveReferenceImage: noop, onOpenSketch: noop,
  }));
  assert.match(markup, /data:image\/png;base64,bWFzaw==/);
  assert.match(markup, /预览标注遮罩/);
});
