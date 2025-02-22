import requests

def download_pdfs_from_list(url_file, output_dir):
    with open(url_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    for url in urls:
        # Download each pdf
        filename = url.split('/')[-1]
        response = requests.get(url)
        # Save to data/pdf
        with open(f"{output_dir}/{filename}", "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"Downloaded {filename}")

if __name__ == "__main__":
    # Example usage:
    download_pdfs_from_list("scripts/config/pdf_urls.txt", "data/pdf")