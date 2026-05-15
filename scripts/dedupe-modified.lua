-- Suppress `date-modified` when it equals `date`. Pure-CSS can't compare two
-- elements' contents, so we strip the metadata before Quarto builds the
-- title block. Compares date-only (first 10 chars) so a YAML `'2026-05-13'`
-- still matches an auto-resolved `last-modified` datetime on the same day.

local function date_only(s)
  return tostring(s):sub(1, 10)
end

function Meta(meta)
  if meta.date and meta["date-modified"] then
    local d1 = date_only(pandoc.utils.stringify(meta.date))
    local d2 = date_only(pandoc.utils.stringify(meta["date-modified"]))
    if d1 == d2 then
      meta["date-modified"] = nil
    end
  end
  return meta
end
