import os
import json
import subprocess
import fitz  # PyMuPDF library for reading PDF files
import requests
import re
import time

def read_pdf_text(pdf_path):
    text = ''
    try:
        pdf_document = fitz.open(pdf_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF file {pdf_path}: {str(e)}")
    return text

def read_txt_text(txt_path):
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except Exception as e:
        print(f"Error reading TXT file {txt_path}: {str(e)}")
        return ''

def split_text_into_paragraphs_and_remove_colons(text, SIZE=10):
    paragraphs = [re.sub(r':', '', paragraph.strip()) for paragraph in text.split('\n') if paragraph.strip()]
    
    merged_paragraphs = []
    current_paragraph = ""

    for paragraph in paragraphs:
        if len(paragraph.split()) < SIZE:
            current_paragraph += " " + paragraph
        else:
            if current_paragraph:
                merged_paragraphs.append(current_paragraph.strip())
                current_paragraph = ""
            merged_paragraphs.append(paragraph)

    if current_paragraph:
        merged_paragraphs.append(current_paragraph.strip())
    
    return merged_paragraphs

def send_to_translation_api(paragraphs):
    api_url = "https://trusting-inherently-feline.ngrok-free.app/translate"
    headers = {'Content-Type': 'application/json'}
    payload = {'texts': paragraphs}
    
    print(f"Sending paragraph {paragraphs}")
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    return response.json()

def process_files(input_folder, output_folder):
    pdf_files = [file for file in os.listdir(input_folder) if file.endswith('.pdf')]
    txt_files = [file for file in os.listdir(input_folder) if file.endswith('.txt')]
    
    for pdf_file in pdf_files + txt_files:
        file_path = os.path.join(input_folder, pdf_file)
        
        if pdf_file.endswith('.pdf'):
            text = read_pdf_text(file_path)
        elif pdf_file.endswith('.txt'):
            text = read_txt_text(file_path)
        
        paragraphs = split_text_into_paragraphs_and_remove_colons(text)
        
        batch_size = 5  # Adjust batch size as needed
        translated_text = []

        for i in range(0, len(paragraphs), batch_size):
            batch_paragraphs = paragraphs[i:i+batch_size]
            
            # Measure time before sending the request
            start_time = time.time()
            
            response = send_to_translation_api(batch_paragraphs)
            
            # Measure time after receiving the response
            end_time = time.time()
            
            print(f"Time taken for batch {i+1}-{min(i+batch_size, len(paragraphs))}: {end_time - start_time:.2f} seconds")
            
            translated_text.extend(response['translations'])
        
        output_text = '\n'.join(translated_text)
        output_file = os.path.join(output_folder, f"{pdf_file}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)

if __name__ == "__main__":
    input_folder = "input"
    output_folder = "output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    process_files(input_folder, output_folder)
