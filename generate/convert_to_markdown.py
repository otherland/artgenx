import shutil
import os
from bs4 import BeautifulSoup
from markdownify import markdownify
from datetime import datetime
import yaml

def process_html_file(html_path):
    with open(html_path, 'r', encoding='utf-8') as html_file:
        html_content = html_file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = soup.find('title').get_text()
    description = soup.find('meta', attrs={'name': 'description'})['content']
    canonical_link = soup.find('link', rel='canonical')['href']
    slug = canonical_link.split('/')[-2]
    
    # Ignore specific part
    for unwanted in soup.select("div#jp-relatedposts"):
        unwanted.extract()

    for unwanted in soup.select("div.heateor_sss_sharing_title"):
        unwanted.extract()

    # Extract h1 tag (assuming there's only one h1 tag)
    try:
        h1_tag = soup.find('h1').get_text()
    except AttributeError:
        h1_tag = title
    

    # Remove h1 tag from entry content
    entry_content = soup.find('div', class_='entry-content')
    if not entry_content:
        entry_content = soup.find('div', class_='article-content')
    h1_tag_element = entry_content.find('h1')
    if h1_tag_element:
        h1_tag_element.extract()

    # for img_tag in entry_content:
    #     img_url = img_tag.get("src")
    #     if img_url:
    #         img_url = base_url + img_url if not img_url.startswith("http") else img_url
    #         response = requests.head(img_url)
    #         if response.status_code != 200:
    #             img_tag.extract()

    
    markdown_content = markdownify(str(entry_content))  # Convert HTML to Markdown

    return title, description, slug, h1_tag, markdown_content

def generate_markdown_file(md_path, title, description, slug, h1_tag, markdown_content, categories):
    date = datetime.now().strftime('%Y-%m-%d')

    front_matter = {
        'title': title,
        'date': date,
        'description': description,
        'draft': False,
        'categories': categories,
        'url': slug,
    }
    
    front_matter_str = yaml.dump(front_matter, default_style="'").strip()  # Remove trailing newline
    
    md_content = f'---\n{front_matter_str}\n---\n \n{markdown_content}'
    
    with open(md_path, 'w', encoding='utf-8') as md_file:
        md_file.write(md_content)

def process_directory(root_dir, markdown_output_folder, categories):
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if filename == 'index.html':
                html_path = os.path.join(root, filename)
                try:
                    title, description, slug, h1_tag, markdown_content = process_html_file(html_path)
                except Exception as e:
                    print(f'Error with file {files} {root}')
                    print(e)
                    continue
                md_filename = f'{slug}.md'
                md_path = os.path.join(root, md_filename)
                generate_markdown_file(md_path, title, description, slug, h1_tag, markdown_content, categories)
                print(f'Converted {html_path} to {md_path}')

    # Create duplicate folder structure for markdown files
    # Copy all generated markdown files to the specified output folder
    os.makedirs(markdown_output_folder, exist_ok=True)

    for root, _, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith('.md'):
                md_path = os.path.join(root, filename)
                new_md_path = os.path.join(markdown_output_folder, filename)
                shutil.copy(md_path, new_md_path)
                print(f'Copied {md_path} to {new_md_path}')

if __name__ == "__main__":
    root_directory = "/Users/admin/Documents/CODE/archives/websites/vitalmayfair.com/"
    markdown_output_folder = "/Users/admin/artgenz/sites/vitalmayfair-website/site/content/posts"
    categories = ["Health"]
    process_directory(root_directory, markdown_output_folder, categories)
