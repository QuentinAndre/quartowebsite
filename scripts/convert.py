"""
Convert Hugo Academic content to Quarto website format.

Reads content from ../Website/ and writes converted .qmd files to ../WebsiteQuarto/.
"""

import os
import re
import shutil
import yaml

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
HUGO_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "Website")
QUARTO_DIR = PROJECT_DIR

HUGO_CONTENT = os.path.join(HUGO_DIR, "content")

# Publication type mapping (Hugo Academic convention)
PUB_TYPE_MAP = {
    0: "Uncategorized",
    1: "Conference Paper",
    2: "Journal Article",
    3: "Working Paper",
    4: "Report",
    5: "Book",
    6: "Book Section",
    7: "Thesis",
    8: "Patent",
}


def split_frontmatter(text):
    """Split a Hugo markdown file into (frontmatter_str, body)."""
    # Match opening --- then content then closing ---
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return None, text


def replace_ref_shortcodes(body):
    """Replace Hugo ref shortcodes with relative URLs.

    {{< ref "/post/slug" >}} -> /posts/slug/
    {{< ref "/publication/slug" >}} -> /publications/slug/
    """
    def ref_replacer(match):
        path = match.group(1).strip().strip('"').strip("'")
        # /post/slug -> /posts/slug/
        if path.startswith("/post/"):
            slug = path[len("/post/"):]
            return f"/posts/{slug}/"
        elif path.startswith("/publication/"):
            slug = path[len("/publication/"):]
            return f"/publications/{slug}/"
        elif path.startswith("/software/"):
            slug = path[len("/software/"):]
            return f"/software/{slug}/"
        else:
            return path

    # Match {{< ref "..." >}} or {{< ref "/post/slug" >}}
    body = re.sub(
        r'\{\{<\s*ref\s+([^>]+?)\s*>\}\}',
        ref_replacer,
        body
    )
    return body


def replace_codepen_shortcodes(body):
    """Replace Hugo codepen shortcode with Quarto shortcode syntax.

    {{< codepen id="XWXxeVB" >}} -> {{< codepen XWXxeVB >}}
    """
    body = re.sub(
        r'\{\{<\s*codepen\s+id="([^"]+)"\s*>\}\}',
        r'{{< codepen \1 >}}',
        body
    )
    return body


def check_featured_image(src_dir):
    """Check if a featured image exists and return its filename."""
    for ext in ["jpg", "jpeg", "png", "gif"]:
        fname = f"featured.{ext}"
        if os.path.exists(os.path.join(src_dir, fname)):
            return fname
    return None


def convert_publication(slug, src_dir, dest_dir):
    """Convert a Hugo Academic publication to Quarto format."""
    src_file = os.path.join(src_dir, "index.md")
    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    fm_str, body = split_frontmatter(text)
    if fm_str is None:
        print(f"  WARNING: No frontmatter found in {src_file}")
        return

    fm = yaml.safe_load(fm_str)
    if fm is None:
        fm = {}

    # Build new frontmatter
    new_fm = {}

    if "title" in fm:
        new_fm["title"] = fm["title"]

    if "authors" in fm:
        new_fm["author"] = fm["authors"]

    if "date" in fm:
        new_fm["date"] = str(fm["date"])

    if "doi" in fm and fm["doi"]:
        new_fm["doi"] = fm["doi"]

    if "summary" in fm and fm["summary"]:
        new_fm["description"] = fm["summary"]

    if "abstract" in fm and fm["abstract"]:
        new_fm["abstract"] = fm["abstract"]

    # Publication type
    if "publication_types" in fm and fm["publication_types"]:
        pub_types = fm["publication_types"]
        cats = [PUB_TYPE_MAP.get(t, "Uncategorized") for t in pub_types]
        new_fm["categories"] = cats

    # Publication venue
    if "publication" in fm and fm["publication"]:
        new_fm["publication"] = fm["publication"]
    if "publication_short" in fm and fm["publication_short"]:
        new_fm["publication-short"] = fm["publication_short"]

    # Tags
    if "tags" in fm and fm["tags"]:
        new_fm["tags"] = fm["tags"]

    # Featured image
    featured = check_featured_image(src_dir)
    if featured:
        preview_only = True
        if isinstance(fm.get("image"), dict):
            preview_only = fm["image"].get("preview_only", True)
        if not preview_only:
            new_fm["image"] = featured

    # URL fields - make pdf relative
    if "url_pdf" in fm and fm["url_pdf"]:
        pdf_path = fm["url_pdf"]
        # If it starts with 'publication/<slug>/', make relative
        if pdf_path.startswith("publication/"):
            pdf_basename = os.path.basename(pdf_path)
            new_fm["url-pdf"] = pdf_basename
        else:
            new_fm["url-pdf"] = pdf_path

    if "url_code" in fm and fm["url_code"]:
        new_fm["url-code"] = fm["url_code"]

    if "url_dataset" in fm and fm["url_dataset"]:
        new_fm["url-dataset"] = fm["url_dataset"]

    if "url_video" in fm and fm["url_video"]:
        new_fm["url-video"] = fm["url_video"]

    # Custom links (like Notebook links)
    if "links" in fm and fm["links"]:
        link_list = []
        for link in fm["links"]:
            if isinstance(link, dict) and "name" in link and "url" in link:
                lnk = {"text": link["name"], "href": link["url"]}
                # Make relative URLs relative to new location
                if lnk["href"].startswith("publication/"):
                    lnk["href"] = os.path.basename(lnk["href"])
                link_list.append(lnk)
        if link_list:
            new_fm["links"] = link_list

    # Write output
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, "index.qmd")

    with open(dest_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(new_fm, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        f.write("---\n")
        if body.strip():
            f.write(body)

    # Copy sibling files
    copy_sibling_files(src_dir, dest_dir)
    print(f"  Converted publication: {slug}")


def convert_post(slug, src_dir, dest_dir):
    """Convert a Hugo Academic blog post to Quarto format."""
    src_file = os.path.join(src_dir, "index.md")
    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    fm_str, body = split_frontmatter(text)
    if fm_str is None:
        print(f"  WARNING: No frontmatter found in {src_file}")
        return

    fm = yaml.safe_load(fm_str)
    if fm is None:
        fm = {}

    # Build new frontmatter
    new_fm = {}

    if "title" in fm:
        new_fm["title"] = fm["title"]

    if "subtitle" in fm and fm["subtitle"]:
        new_fm["subtitle"] = fm["subtitle"]

    if "authors" in fm:
        new_fm["author"] = fm["authors"]

    if "date" in fm:
        new_fm["date"] = str(fm["date"])

    if "lastmod" in fm and fm["lastmod"]:
        new_fm["date-modified"] = str(fm["lastmod"])

    if "summary" in fm and fm["summary"]:
        new_fm["description"] = fm["summary"]

    if "tags" in fm and fm["tags"]:
        new_fm["tags"] = fm["tags"]

    if "categories" in fm and fm["categories"]:
        new_fm["categories"] = fm["categories"]

    if "toc" in fm:
        new_fm["toc"] = fm["toc"]

    if "draft" in fm and fm["draft"]:
        new_fm["draft"] = fm["draft"]

    # Featured image
    featured = check_featured_image(src_dir)
    if featured:
        preview_only = False
        if isinstance(fm.get("image"), dict):
            preview_only = fm["image"].get("preview_only", False)
        if not preview_only:
            new_fm["image"] = featured

    # Apply shortcode replacements to body
    body = replace_ref_shortcodes(body)
    body = replace_codepen_shortcodes(body)

    # Write output
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, "index.qmd")

    with open(dest_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(new_fm, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        f.write("---\n")
        if body.strip():
            f.write(body)

    # Copy sibling files
    copy_sibling_files(src_dir, dest_dir)
    print(f"  Converted post: {slug}")


def convert_software(slug, src_dir, dest_dir):
    """Convert a Hugo Academic software page to Quarto format."""
    src_file = os.path.join(src_dir, "index.md")
    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    fm_str, body = split_frontmatter(text)
    if fm_str is None:
        print(f"  WARNING: No frontmatter found in {src_file}")
        return

    fm = yaml.safe_load(fm_str)
    if fm is None:
        fm = {}

    # Build new frontmatter
    new_fm = {}

    if "title" in fm:
        new_fm["title"] = fm["title"]

    if "subtitle" in fm and fm["subtitle"]:
        new_fm["subtitle"] = fm["subtitle"]

    if "summary" in fm and fm["summary"]:
        new_fm["description"] = fm["summary"]

    if "toc" in fm:
        new_fm["toc"] = fm["toc"]

    # Image as title banner
    if fm.get("image_as_title"):
        featured = check_featured_image(src_dir)
        if featured:
            new_fm["title-block-banner"] = featured

    # Generate links HTML block to prepend to body
    links_html = ""
    if "links" in fm and fm["links"]:
        links_html = '<div class="software-links" style="margin-bottom: 1.5em;">\n'
        for link in fm["links"]:
            if isinstance(link, dict) and "name" in link and "url" in link:
                name = link["name"]
                url = link["url"]
                links_html += f'<a href="{url}" class="btn btn-outline-primary btn-sm" target="_blank" rel="noopener">{name}</a>\n'
        links_html += '</div>\n\n'

    # Apply shortcode replacements to body
    body = replace_ref_shortcodes(body)
    body = replace_codepen_shortcodes(body)

    # Write output
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, "index.qmd")

    with open(dest_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(new_fm, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        f.write("---\n")
        if links_html:
            f.write("\n")
            f.write(links_html)
        if body.strip():
            f.write(body)

    # Copy sibling files
    copy_sibling_files(src_dir, dest_dir)
    print(f"  Converted software: {slug}")


def copy_sibling_files(src_dir, dest_dir):
    """Copy all files except index.md from src_dir to dest_dir, including subdirs."""
    for item in os.listdir(src_dir):
        if item == "index.md":
            continue
        if item == "header.md":
            continue
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(dest_dir, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dest_path)


def main():
    print("=== Hugo Academic -> Quarto Conversion ===\n")

    # Convert publications
    pub_src = os.path.join(HUGO_CONTENT, "publication")
    pub_dest = os.path.join(QUARTO_DIR, "publications")
    print("Converting publications...")
    if os.path.exists(pub_src):
        for slug in sorted(os.listdir(pub_src)):
            src_dir = os.path.join(pub_src, slug)
            if os.path.isdir(src_dir) and os.path.exists(os.path.join(src_dir, "index.md")):
                dest_dir = os.path.join(pub_dest, slug)
                convert_publication(slug, src_dir, dest_dir)

    # Convert posts
    post_src = os.path.join(HUGO_CONTENT, "post")
    post_dest = os.path.join(QUARTO_DIR, "posts")
    print("\nConverting blog posts...")
    if os.path.exists(post_src):
        for slug in sorted(os.listdir(post_src)):
            src_dir = os.path.join(post_src, slug)
            if os.path.isdir(src_dir) and os.path.exists(os.path.join(src_dir, "index.md")):
                dest_dir = os.path.join(post_dest, slug)
                convert_post(slug, src_dir, dest_dir)

    # Convert software
    sw_src = os.path.join(HUGO_CONTENT, "software")
    sw_dest = os.path.join(QUARTO_DIR, "software")
    print("\nConverting software pages...")
    if os.path.exists(sw_src):
        for slug in sorted(os.listdir(sw_src)):
            src_dir = os.path.join(sw_src, slug)
            if os.path.isdir(src_dir) and os.path.exists(os.path.join(src_dir, "index.md")):
                dest_dir = os.path.join(sw_dest, slug)
                convert_software(slug, src_dir, dest_dir)

    print("\n=== Conversion complete! ===")


if __name__ == "__main__":
    main()
