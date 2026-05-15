-- Auto-render publication page bodies from YAML metadata.
-- Triggers on any document whose YAML includes a `publication:` field
-- (i.e. the per-paper index.qmd files under publications/*/). The listing
-- page (publications/index.qmd) has no `publication:` field and is skipped.
--
-- Appends, in order:
--   1. Author line (bold)
--   2. ## Abstract + abstract text
--   3. Pill-button row (Manuscript / Appendix / Code / DOI)
--   4. Inline PDF iframe

local function stringify(x)
  if not x then return nil end
  return pandoc.utils.stringify(x)
end

local function meta_to_string_list(m)
  if not m then return {} end
  if type(m) == "string" then return { m } end
  -- MetaList: iterate; MetaInlines: stringify whole.
  if m.t == "MetaInlines" or m.t == "MetaBlocks" then
    return { stringify(m) }
  end
  local out = {}
  for _, v in ipairs(m) do
    table.insert(out, stringify(v))
  end
  return out
end

local function html_attr(s)
  return tostring(s):gsub("&", "&amp;"):gsub('"', "&quot;")
end

function Pandoc(doc)
  local meta = doc.meta
  if not meta.publication then return doc end

  -- Author line
  if meta.author then
    local authors = meta_to_string_list(meta.author)
    if #authors > 0 then
      local line = "**" .. table.concat(authors, ", ") .. "**"
      local parsed = pandoc.read(line, "markdown").blocks
      for _, b in ipairs(parsed) do table.insert(doc.blocks, b) end
    end
  end

  -- Abstract
  if meta.abstract then
    table.insert(doc.blocks, pandoc.Header(2, { pandoc.Str("Abstract") }))
    local abs = stringify(meta.abstract)
    table.insert(doc.blocks, pandoc.Para({ pandoc.Str(abs) }))
  end

  -- Button row
  local btns = {}
  local function add_btn(url, icon, label)
    if url then
      local href = html_attr(stringify(url))
      table.insert(btns,
        '<a href="' .. href .. '" class="pub-btn" target="_blank" rel="noopener">' ..
        '<i class="bi ' .. icon .. '"></i> ' .. label .. '</a>')
    end
  end
  add_btn(meta["url-pdf"],      "bi-file-earmark-pdf",  "Manuscript")
  add_btn(meta["url-appendix"], "bi-file-earmark-text", "Appendix")
  add_btn(meta["url-code"],     "bi-box-arrow-up-right", "Code / OSF")
  if meta.doi then
    local doi = stringify(meta.doi)
    table.insert(btns,
      '<a href="https://doi.org/' .. html_attr(doi) ..
      '" class="pub-btn" target="_blank" rel="noopener">' ..
      '<i class="bi bi-link-45deg"></i> DOI</a>')
  end
  if #btns > 0 then
    local html = '<div class="pub-buttons">\n' .. table.concat(btns, "\n") .. "\n</div>"
    table.insert(doc.blocks, pandoc.RawBlock("html", html))
  end

  -- PDF embed
  if meta["url-pdf"] then
    local pdf = html_attr(stringify(meta["url-pdf"]))
    local iframe = '<iframe src="' .. pdf ..
      '" class="pub-pdf-embed" title="Manuscript PDF" loading="lazy"></iframe>'
    table.insert(doc.blocks, pandoc.RawBlock("html", iframe))
  end

  return doc
end
