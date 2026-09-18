# 出海ID指南（chuhaiid.github.io）

淘号号的站外卫星站。**目的是抢商业词排名，把人送到主站**，不是内容站。
线上：https://chuhaiid.github.io/

---

## 日常流程（每天只做这四步）

```sh
cd /Users/dwan/Project/taozi277/chuhaiid
export PATH="/Library/Developer/CommandLineTools/usr/bin:$PATH"   # 本机 git 必须加,否则被 Xcode 许可拦

python3.12 build.py --new appleid change-region   # 1. 建空文章
# 2. 编辑 appleid/change-region.html：改 4 个 meta + 正文
python3.12 build.py                                # 3. 索引页/首页/sitemap 自动更新
git add -A && git commit -m "..." && git push      # 4. 推送,1-2 分钟上线
```

**新建文章只需要改 4 个地方**（模板顶部有醒目标注）：`title`、`description`、`excerpt`、`group`，然后写正文。索引页、首页、sitemap、导航、页脚全部自动生成，不要手改。

---

## 命令

| 命令 | 作用 |
| --- | --- |
| `build.py` | 重建所有索引页、首页、sitemap，统一全站导航与页脚 |
| `build.py --check` | 只报告会改什么，不写盘 |
| `build.py --new <品类> <slug>` | 用模板新建空文章 |

品类：`appleid` `telegram` `twitter` `gmail` `facebook`

---

## 目录结构

```
site.json        站点与品类配置（改导航、CTA、分组都在这里）
build.py         生成器
_template.html   新文章模板
assets/style.css 全站样式
<品类>/index.html  自动生成，别手改
<品类>/*.html      文章，手写
index.html       自动生成，别手改
sitemap.xml      自动生成，别手改
```

**加新品类**：在 `site.json` 的 `categories` 里加一项，跑 `build.py`，目录和索引页自动出现。

---

## 写作红线

1. **不写任何价格**（同 `/gxid` 铁律）
2. **只借题不借文**——竞品的选题可以用，正文必须重写。照搬等于给 Google 送重复内容
3. **整页只能有一个 h1**
4. 每篇至少 **2 条站内内链 + 1 个 CTA**
5. 不编造数据、不写虚假评价、不写「与各平台无利益关系」这类假话
6. 榜单页必须列**真实**同行，只给自家一条链接（业主 2026-09-16 拍板同意提竞品名）

---

## 选题来源

| 来源 | 位置 |
| --- | --- |
| appleshow 27 页标题清单 | 竞品站 `sites.google.com/view/appleshow` |
| svip.chat 博客 360 篇 | `docs/方案/SEO/appleid-seo/svip-blog-选题库-2026-09-10.md`（带「状态」列记已认领）|
| fbguanggao 28 页 | 竞品站 `sites.google.com/view/fbguanggao` |

**发前必须比对主站已发文章，避免撞题。**主站苹果专项已发 11 篇（`/news/37 39 40 41 42 43 44 45 46 50` 等）。

---

## 为什么是这个形态

2026-09-16 实测：中文账号品类的商业词第一名几乎全是卫星站，不是商家自有域名。

| 品类 | 第一名 | 页数 |
| --- | --- | --- |
| 苹果 ID | `sites.google.com/view/appleshow` | 27 |
| Facebook | `sites.google.com/view/fbguanggao` | 28 |
| Gmail | `sites.google.com/view/gugezhanghaogoumai` | **9** |
| 推特 | `twitteraccount.github.io` | 11 |

结论：①页数门槛随品类竞争强度变化，9 页就可能够；②成功案例全是单品类聚焦站；③结构一律「教程页养站 + 少数销售页收口」；④榜单页只给一条外链给金主，其余同行纯文字陪跑。

**目标 20 篇/品类。节奏由业主定，不自行加量。**

---

## 部署

- 仓库 `chuhaiid/chuhaiid.github.io`，鉴权走 **deploy key**（不是 PAT）
- 私钥 `~/.ssh/id_ed25519_chuhaiid`，SSH 别名 `github-chuhaiid`，只能推这一个仓库
- git 身份 `chuhaiid@users.noreply.github.com`（公开仓库，不暴露业主邮箱）
- push 后 1–2 分钟自动上线，无需任何手动开关

## 与 Google Sites 的分工

Google Sites **没有可用 API**（官方 API 只支持 2016 年前的 Classic Sites），只能业主人工把 HTML 粘进「嵌入代码」框。
所以：**Sites 由 Claude 写 HTML、业主手动粘；GitHub Pages 由 Claude 全自动完成。**
