import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import pypandoc 
import pytesseract
import cv2 

UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, 
     resources={r"/api/*": {"origins": "http://localhost:5173"}}, 
     expose_headers=['Content-Disposition'])

def preprocess_image_for_ocr(image_path):
    """
    Carrega uma imagem e aplica uma estratégia de pré-processamento de
    suavização seguida de binarização global para melhorar o OCR.
    """
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Etapa 1: Suavização com Gaussian Blur para reduzir o ruído do fundo
    # O kernel (5,5) define a intensidade do desfoque.
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    
    # Etapa 2: Binarização Global com o método de Otsu
    # Otsu analisa a imagem e encontra o melhor valor de limiar global automaticamente.
    # O resultado é uma imagem limpa em preto e branco.
    _, binary_image = cv2.threshold(
        blurred_image, 
        0, 
        255, 
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    
    return binary_image 


def handle_pdf_to_png(file_path, output_folder):
    try:
        images = convert_from_path(file_path, first_page=1, last_page=1)
        if not images:
            return None, None
        
        first_page_image = images[0]
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        output_filename = f"{base_filename}_page_1.png"
        output_path = os.path.join(output_folder, output_filename)
        first_page_image.save(output_path, 'PNG')
        
        return output_path, output_filename
    except Exception as e:
        print(f"Erro durante a conversão de PDF para PNG: {e}")
        return None, None

def handle_docx_to_txt(file_path, output_folder):
    try:
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        output_filename = f"{base_filename}.txt"
        output_path = os.path.join(output_folder, output_filename)

        pypandoc.convert_file(file_path, 'plain', outputfile=output_path)
        
        print(f"Conversão para TXT bem-sucedida. Arquivo salvo em: {output_path}")
        return output_path, output_filename
    except Exception as e:
        print(f"Erro durante a conversão de DOCX para TXT: {e}")
        return None, None

def handle_image_to_text(file_path, output_folder):
    try:
        processed_image = preprocess_image_for_ocr(file_path)

        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        debug_filename = f"{base_filename}_processada.jpg"
        debug_path = os.path.join(output_folder, debug_filename)
        cv2.imwrite(debug_path, processed_image)
        print(f"IMAGEM DE DEBUG SALVA EM: {debug_path}")

        extracted_text = pytesseract.image_to_string(processed_image, lang='por')

        output_filename = f"{base_filename}_transcrito.txt"
        output_path = os.path.join(output_folder, output_filename)

        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(extracted_text)
            
        print(f"OCR bem-sucedido. Texto salvo em: {output_path}")
        return output_path, output_filename
    except Exception as e:
        print(f"Erro durante o OCR: {e}")
        return None, None

@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    conversion_type = request.form.get('conversionType')

    if file.filename == '' or conversion_type is None:
        return jsonify({"error": "Parâmetros faltando"}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(file_path)
        print(f"Arquivo '{filename}' salvo para conversão '{conversion_type}'")

        output_path = None
        output_filename = None

        if conversion_type == 'pdf-to-png':
            output_path, output_filename = handle_pdf_to_png(file_path, app.config['UPLOAD_FOLDER'])
        elif conversion_type == 'docx-to-txt':
            output_path, output_filename = handle_docx_to_txt(file_path, app.config['UPLOAD_FOLDER'])
        elif conversion_type == 'img-to-text':
            output_path, output_filename = handle_image_to_text(file_path, app.config['UPLOAD_FOLDER'])
        else:
            return jsonify({"error": f"Tipo de conversão '{conversion_type}' não suportado"}), 400

        if output_path and output_filename:
            try:
                return send_file(
                    output_path, 
                    as_attachment=True,
                    download_name=output_filename
                )
            except Exception as e:
                print(f"Erro ao enviar o arquivo: {e}")
                return jsonify({"error": "Não foi possível enviar o arquivo"}), 500
        else:
            return jsonify({"error": "Falha ao converter o arquivo. O formato é suportado?"}), 500
    
    return jsonify({"error": "Ocorreu um erro inesperado"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)