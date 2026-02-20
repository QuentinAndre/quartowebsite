-- CodePen embed shortcode for Quarto
-- Usage: {{< codepen PENID >}}
-- Renders a CodePen embed iframe

return {
  ['codepen'] = function(args)
    local pen_id = pandoc.utils.stringify(args[1])
    if pen_id == "" then
      return pandoc.Null()
    end

    local user = "QuentinAndre"

    local html = string.format(
      '<p class="codepen" data-height="500" data-default-tab="result" data-slug-hash="%s" data-user="%s" style="height: 500px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border: 2px solid; margin: 1em 0; padding: 1em;">\n' ..
      '  <span>See the Pen <a href="https://codepen.io/%s/pen/%s">%s</a> by %s (<a href="https://codepen.io/%s">@%s</a>) on <a href="https://codepen.io">CodePen</a>.</span>\n' ..
      '</p>\n' ..
      '<script async src="https://cpwebassets.codepen.io/assets/embed/ei.js"></script>',
      pen_id, user, user, pen_id, pen_id, user, user, user
    )

    return pandoc.RawBlock("html", html)
  end
}
