-- Auto-render publication page bodies from YAML metadata.
-- Triggers on any document whose YAML includes a `publication:` field
-- (i.e. the per-paper index.qmd files under publications/*/). The listing
-- page (publications/index.qmd) has no `publication:` field and is skipped.
--
-- Quarto already renders title, authors, date, DOI, description, and the
-- abstract from YAML, so this filter only appends:
--   1. Pill-button row (Manuscript / Appendix / Code) — no DOI button,
--      DOI is shown by Quarto in the title-block meta line.
--   2. Inline PDF iframe.

local function stringify(x)
  if not x then return nil end
  return pandoc.utils.stringify(x)
end

local function html_attr(s)
  return tostring(s):gsub("&", "&amp;"):gsub('"', "&quot;")
end

function Pandoc(doc)
  local meta = doc.meta
  if not meta.publication then return doc end

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
