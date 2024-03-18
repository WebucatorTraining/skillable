import re
import sys
import os
import shutil
import zipfile
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as md
from lxml import etree


def rename_and_unzip_epub(epub_file_path):
    # Check if the file exists
    if not os.path.isfile(epub_file_path):
        print(f"The file {epub_file_path} does not exist.")
        return

    # Extract the base name (without extension) and directory of the epub file
    base_name = os.path.splitext(os.path.basename(epub_file_path))[0]
    directory = os.path.dirname(epub_file_path)

    # Define the new zip file path
    zip_file_path = os.path.join(directory, base_name + ".zip")

    # Rename the epub file to a zip file
    # os.rename(epub_file_path, zip_file_path)
    shutil.copy2(epub_file_path, zip_file_path)

    print(f"Renamed '{epub_file_path}' to '{zip_file_path}'.")

    # Create the target directory for the unzipped content
    # Get the absolute path of 'directory'
    absolute_directory = os.path.abspath(directory)

    # Move up one directory from 'absolute_directory'
    parent_directory = os.path.dirname(absolute_directory)

    # Now, create 'target_dir' in the parent directory
    target_dir = os.path.join(parent_directory, base_name, "epub")

    os.makedirs(target_dir, exist_ok=True)

    # Unzip the file
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    print(f"Extracted '{zip_file_path}' to '{target_dir}'.")


def is_valid_xml(content):
    """
    Check if the given content is valid XML.

    Args:
    - content (str): The content to be checked for XML validity.

    Returns:
    - bool: True if the content is valid XML, False otherwise.
    """
    try:
        # If content is not bytes, encode it to bytes
        if not isinstance(content, bytes):
            content = content.encode("utf-8")
        etree.fromstring(content)
        return True
    except etree.XMLSyntaxError:
        return False


def build_and_replace_nav_items(markdown_content):
    """
    Find lines starting with "Lab " or "Exercise " followed by a digit and build a navigation items string.
    Replace "REPLACENAV" in the markdown content with the navigation items string.

    Args:
    - markdown_content (str): The markdown content to process.

    Returns:
    - str: The modified markdown content with navigation items added.
    """
    # Find all lines starting with "Lab \d" or "Exercise \d"
    pattern = re.compile(r"^(# Lab \d+|# Lab [A-Z]|# Exercise \d+)(.+)$", re.MULTILINE)
    matches = pattern.findall(markdown_content)

    # Build navigation items string
    nav_items = []
    for match in matches:
        prefix, title = match
        prefix = prefix[2:]
        # Create a slug for the navigation link
        slug = "-".join(prefix.lower().split()) + "-" + "-".join(title.lower().split())
        slug = slug.replace("-:-", "-")
        slug = slug.replace("[", "")
        slug = slug.replace("]", "")
        nav_item = f"> 1. [{prefix}{title}](#{slug})"
        nav_items.append(nav_item)

    nav_items_string = "\n".join(nav_items)

    # Replace "REPLACENAV" with the navigation items string
    markdown_content = markdown_content.replace("REPLACENAV", nav_items_string)

    return markdown_content


def convert_html_to_md(input_html_file):
    """
    Convert the content of an HTML file to Markdown format and prepend a preamble.
    Additional processing is applied to the markdown content.

    Args:
    - input_html_file (str): The path to the input HTML file.

    Side effects:
    - Writes the converted markdown content to a file with the same name as the input file, but with a .md extension.
    - Prints the name of the created Markdown file.
    """
    encodings = ["utf-8", "iso-8859-1", "cp1252"]
    course_num = input_html_file.split(".")[0]

    preamble = f"""# Home
## COURSE_NAME ({course_num})

<img src="https://static.webucator.com/media/public/materials/cover_images/PATH_TO_IMAGE.png"
  alt="Courseware Cover" />

---

*This lab environment was created for courseware purchased on www.coursewarestore.com.*

<link rel="stylesheet" href="https://raw.githubusercontent.com/WebucatorTraining/skillable/combined-knowledge/stylesheet.css">
===

# Activating Your Software for Class
[Home](#home)

[!include [Finding Your Password](https://raw.githubusercontent.com/WebucatorTraining/skillable/main/365-password.md)]

Please note the following differences between this virtual desktop and the course manual:

1. Your lab files can be found on **C:\\Labs**.
2. We will skip labs 0 and 1 in the manual as they relate to setting up the environment. Your environment is already
set up.

Proceed to Lab 2 to begin your first exercise, noting that Power BI is already open in your browser, you are not
required to use the app launcher to navigate there.

===

"""

    html_content = None
    for encoding in encodings:
        try:
            with open(input_html_file, "r", encoding=encoding) as file:
                html_content = file.read()
            break
        except UnicodeDecodeError:
            pass

    if html_content is None:
        print("Failed to read the file with supported encodings.")
        return

    # Initialize BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove all <body> tags
    for body_tag in soup.find_all("body"):
        body_tag.unwrap()

    # Convert specific <p> tags to Markdown headers
    for p_tag in soup.find_all("p"):
        if re.match(r"(Exercise \d+|Lab [A-Z0-9]+)", p_tag.text.strip()):
            # Create a new <h1> tag
            h1_tag = soup.new_tag("h1")
            # Transfer the text from the <p> tag to the new <h1> tag
            h1_tag.string = p_tag.text.strip()
            # Replace the <p> tag with the new <h1> tag in the soup object
            p_tag.replace_with(h1_tag)

    markdown_content = preamble + str(soup)
    # Replace lines that contain only whitespace with a newline character
    markdown_content = re.sub(
        r"^\s+$", "\n", markdown_content, flags=re.MULTILINE
    ).strip()

    # Then, replace three or more consecutive newlines with two newlines
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    # Replace h1 tags with markdown
    markdown_content = markdown_content.replace("<h1>", "# ")
    markdown_content = markdown_content.replace("</h1>", "")

    # Always add "===" before "Exercise \d" lines
    markdown_content = re.sub(
        r"^(# Exercise \d)",
        r"===\n[Home](#home)\n\1",
        markdown_content,
        flags=re.MULTILINE,
    )

    markdown_content = re.sub(
        r"^(# Lab [A-Z0-9])",
        r"===\n[Home](#home)\n\1",
        markdown_content,
        flags=re.MULTILINE,
    )

    # Then, replace any instance of "===\n===" with "==="
    markdown_content = re.sub(r"===\n+===", r"===", markdown_content)

    markdown_content = markdown_content.replace(
        "\n===",
        "\n\n>[+] Exercise List (Click to Open)\n> 1. [Activating Your Software for Class](#activating-your-software-for-class)\nREPLACENAV\n\n===",
    )

    markdown_content = markdown_content.replace(
        'src="images/',
        f'src="https://raw.githubusercontent.com/WebucatorTraining/skillable/main/{course_num}/epub/images/',
    )

    markdown_content = build_and_replace_nav_items(markdown_content)

    output_md_file = input_html_file.rsplit(".", 1)[0] + ".md"

    with open(output_md_file, "w", encoding="utf-8") as file:
        file.write(markdown_content)

    print(f"Markdown file created: {output_md_file}")


def replace_newlines_except_pre(soup_body):
    """
    Replace all newline characters with spaces in the BeautifulSoup object, except within <pre> tags.

    Args:
    - soup_body (BeautifulSoup): The BeautifulSoup body object to process.
    """
    for element in soup_body.descendants:
        if element.name == "pre":  # Skip <pre> tags
            continue
        if isinstance(element, NavigableString):
            s = str(element)
            cleaned_text = s.replace("\n", "")
            element.replace_with(cleaned_text)


def replace_alt_entities(soup):
    """
    Replace newline characters in 'alt' attributes of all elements within the BeautifulSoup object with spaces.

    Args:
    - soup (BeautifulSoup): The BeautifulSoup object to process.
    """
    # Find all elements with an 'alt' attribute
    for tag in soup.find_all(attrs={"alt": True}):
        tag["alt"] = tag["alt"].replace("\n", " ")


def extract_body_content(html_content, file_name):
    """
    Extract the body content from HTML content, processing it to replace newlines and alt attributes as necessary.

    Args:
    - html_content (str): The HTML content to extract the body from.
    - file_name (str): The name of the file, used for warning messages if no body content is found.

    Returns:
    - str: The processed body content of the HTML.
    """
    if is_valid_xml(html_content):
        soup = BeautifulSoup(html_content, "lxml-xml")
    else:
        soup = BeautifulSoup(html_content, "lxml")

    replace_newlines_except_pre(soup)
    replace_alt_entities(soup)

    body_content = soup.body

    if body_content:
        str_body_content = str(body_content)
        return str_body_content
    else:
        print(f"WARNING: {file_name} has no body content.")
        return ""


def should_include_file(html_content):
    """
    Determine if the HTML content should be included based on specific criteria (e.g., contains "Lab 2" at the start of a <p> tag).

    Args:
    - html_content (str): The HTML content to check.

    Returns:
    - bool: True if the file should be included, False otherwise.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    first_p = soup.body.find("p")
    if first_p:
        for child in first_p.children:
            if isinstance(child, NavigableString) and child.strip().startswith("Lab 2"):
                return True
            if isinstance(child, NavigableString) and child.strip().startswith("Lab B"):
                return True
    return False


def combine_html_files(source_directory, result_html_file):
    """
    Combine HTML files from a source directory into a single HTML file, starting from a file that meets specific criteria.

    Args:
    - source_directory (str): The directory containing HTML files to be combined.
    - result_html_file (str): The path to the output HTML file.

    Side effects:
    - Writes the combined HTML content to the specified output file.
    """
    html_files = sorted(
        [f for f in os.listdir(source_directory) if f.endswith(".html")]
    )
    start_combining = False  # Flag to start combining files

    combined_content = ""

    for filename in html_files:
        filepath = os.path.join(source_directory, filename)
        with open(filepath, "r", encoding="utf-8") as infile:
            file_content = infile.read()
            # Check if we should start combining
            if not start_combining:
                start_combining = should_include_file(file_content)
                if not start_combining:
                    print(f"Skipping {filename}")
                    continue  # Skip this file and continue to the next one

            print(f"Including {filename}")

            # If start_combining is True, or once it's set to True, include the file's content
            body_content = extract_body_content(file_content, filename)
            combined_content += body_content + "\n"

    with open(result_html_file, "w", encoding="utf-8") as outfile:
        outfile.write(combined_content)

    soup = BeautifulSoup(combined_content, "html.parser")

    images = soup.find_all("img")

    # The folder containing the images
    images_folder = os.path.join(source_directory, "images")

    # Gather all image names found in the soup object
    image_names_in_soup = {
        os.path.basename(img.get("src")) for img in images if img.get("src")
    }

    # List all image files currently in the images_folder
    image_files_in_folder = {
        file
        for file in os.listdir(images_folder)
        if file.endswith(("jpg", "jpeg", "png", "gif"))
    }

    # Find image files in the folder that are not referenced in the soup
    images_to_delete = image_files_in_folder - image_names_in_soup

    # Delete images not found in soup
    for image_name in images_to_delete:
        image_path = os.path.join(images_folder, image_name)
        os.remove(image_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_markdown_from_epub_files.py <path_to_epub_file>")
        sys.exit(1)

    epub_file_path = sys.argv[1]
    rename_and_unzip_epub(epub_file_path)

    course_num = os.path.splitext(os.path.basename(epub_file_path))[0]
    result_html_file = course_num + ".html"
    path_to_folder = os.path.join(course_num, "epub")
    print(path_to_folder)

    combine_html_files(path_to_folder, result_html_file)
    convert_html_to_md(result_html_file)
