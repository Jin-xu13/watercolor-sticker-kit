# Prompt 配方

所有模板为英文。方括号按实替换。

**调用要点**：用 `background: "opaque"`，并把提示词里的背景要求写成**纯白 `#FFFFFF`**（写 transparent 没用，模型不给你 alpha）。出图后必须跑 `scripts/matte.py`。
第 2 枚起额外传 `image2` = 第 1 枚成品，`input_fidelity` 0.4–0.5。

## S-1 单枚贴纸（标准）

```
One single die-cut watercolour sticker, isolated on a flat pure white (#FFFFFF) background. The white is evenly flat and empty — no gradient, no paper texture, no vignette, no shadow cast on a surface.

Subject: [元素英文描述，含 2-3 个决定辨识度的特征], seen from [角度], with no surroundings, no ground, no environment. The subject is centred and occupies about [80-85 / 55-70]% of the canvas width, with clear empty white margin on all four sides.

Watercolour build, three values only: a very pale first wash (8-15% density) that slightly overruns the silhouette and dries with an uneven edge; a mid-tone second wash (30-45%) that stops short of the highlight areas; and one small dark accent (55-70%) covering no more than a tenth of the subject. Each wash must dry darker along its rim, leaving a fine sediment line. Keep 10-25% of the subject as reserved paper white for highlights — do not paint over them. Allow one or two soft faint blooms. Cold-press watercolour paper grain visible only inside the sticker.

Colours sampled from the source photo, desaturated by roughly 20%: [取色，3-5 个]。The darkest value is [deep blue-grey #2F3742 / warm brown-grey #4A4038], never pure black. One single warm accent allowed: [点缀色].

Cut line: a thick warm-white (#F7F2E8) border follows the silhouette like a hand-cut sticker. Its width varies by about 15% along the contour, corners are rounded, and the outer edge is faintly uneven — not a uniform geometric offset, not a vector outline. A very thin flat drop shadow sits just beneath the sticker at about 12% opacity, tight and soft, floating — never cast onto a surface.

Everything outside the white cut border is the flat empty white background. No square base, no paper backdrop, no ground shadow. No lettering, no logo, no license plate, no frame, no outline stroke. No photorealism, no photo texture, no glossy 3D, no gradients, no vector flat fill, no marker strokes, no ink linework.
```

**出图后必做**：`python <skill>/scripts/matte.py <生成图> <01-xxx.png>`

## S-2 风格锚定（第 2 枚起追加）

在 S-1 末尾追加：

```
The second supplied image is a finished sticker from the same set. Match its watercolour density, its white-border thickness and wobble, its paper grain, its shadow and its colour temperature exactly. Copy the style only — the subject must be the one described above, not the one in that image.
```

## S-3 太大或太小（尺寸纠偏）

```
Rescale the sticker within the canvas: the subject plus its white cut border should occupy [80-85 / 55-70]% of the canvas width, centred, with clear transparent margin on all four sides.
```

## S-4 白底不干净（背景不是死白）

```
The background must be one flat even pure white #FFFFFF with no gradient, no off-white cast, no paper grain, no vignette and no shadow. Replace whatever is behind the sticker with plain empty white. Nothing else in the image changes.
```

## 失败模式对照

| 现象 | 原因 | 用哪条 |
|---|---|---|
| 出的是带底色的方块，不是透明 PNG | **正常现象**，模型永远不出 alpha | 不是提示词问题，跑 `scripts/matte.py` |
| 抠图后白边被吃掉一圈 | 背景不是中性白，或阈值被改宽了 | 用 S-4 重出白底；检查 `MAX_CHROMA` 是否被调大 |
| 抠图后残留白色孤岛 | 孤岛与边缘不连通 | 第二次抠图会报告仍有比例；手工或换 S-4 重出 |
| 背景带渐变／纸纹／暗角 | 模型默认加水彩纸背景 | S-4，明确 `flat even pure white, no paper grain` |
| 变成平涂色块，没有水彩层次 | 三层明度没写清 | 回 S-1 并把「three values only」逐层写浓度 |
| 出现黑色描边 | 模型默认给贴纸上轮廓 | 加 `no outline stroke, no ink linework` |
| 白边宽度完全一致，像图标 | 「offset」被理解成等距扩边 | 强调 `width varies by 15%, hand-cut, uneven outer edge` |
| 画了地面阴影 | 模型默认给物体投影 | 明确 `floating, never cast onto a surface` |
| 主体糊成一团认不出 | 元素特征描述不足 | 补 2–3 个决定辨识度的特征词，重跑 |
| 同一套里颜色不统一 | 没用样张锚定 | 传 `image2` = 样张，加 S-2 |
| **画出来的是别的东西（比如云变成罐车）** | **锚定图与被画对象明度太接近，内容泄漏** | **去掉 `image2`**，只靠色板文字规格统一；并在主体描述里加 `it is a cloud, not an object: no container, no cylinder, no wheels` 这类排除句 |
| 一次生出好几枚 | 提示词里出现了复数或「set」 | 只描述一个主体，删掉任何 set / collection 字样 |
