from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)




model = load_model('model.h5')  # Replace with your model's path

class_labels = ['Syzygium Cumini (Jamun)', 'Ocimum Tenuiflorum (Tulsi)', 'Citrus Limon (Lemon)',
                 'Brassica Juncea (Indian Mustard)', 'Psidium Guajava (Guava)', 'Punica Granatum (Pomegranate)',
                 'Mangifera Indica (Mango)', 'Mentha (Mint)', 'Basella Alba (Basale)', 'Azadirachta Indica (Neem)']
# Replace with actual class labels

def classify_image(img_path):
    img = image.load_img(img_path, target_size=(180, 180))  # Adjust target size to your model's input
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    predictions = model.predict(img_array)
    class_idx = np.argmax(predictions[0])
    return class_labels[class_idx], predictions[0][class_idx]

def scrape_details(class_label):
    # Define URLs for different plants
    urls = {
        "Syzygium Cumini (Jamun)": "https://pubmed.ncbi.nlm.nih.gov/37667613/#:~:text=Leaves%20of%20jamun%20collected%20as,bladder%20stones%20and%20other%20ailments.",
        "Ocimum Tenuiflorum (Tulsi)": "https://www.1mg.com/ayurveda/tulsi-12?wpsrc=Google+Organic+Search",
        "Citrus Limon (Lemon)": "https://www.vietnam.vn/en/la-chanh-giup-giai-cam-tri-ho-va-co-nhieu-loi-ich-cho-suc-khoe-bao-quang-nam-online/#:~:text=In%20addition%2C%20lemon%20leaves%20are%20also%20used%20to%20boil%20cold%20water.&text=Has%20antibacterial%20properties-,Lemon%20leaves%20have%20antibacterial%20properties%20and%20contain%20many%20compounds%20that,limonene%2C%20citral%2C%20and%20geraniol.",
        "Brassica Juncea (Indian Mustard)": "https://www.indiatvnews.com/health/superfood-mustard-greens-know-these-5-benefits-of-sarson-ka-saag-2024-04-16-926450",
        "Psidium Guajava (Guava)": "https://www.healthline.com/nutrition/8-benefits-of-guavas#TOC_TITLE_HDR_2",
        "Punica Granatum (Pomegranate)": "https://www.medindia.net/news/healthwatch/pomegranate-leaves-natures-secret-remedy-for-health-and-wellness-215154-1.htm",
        "Mangifera Indica (Mango)": "https://www.ifp.co.in/health/benefits-of-mango-leaves#google_vignette",
        "Mentha (Mint)": "https://www.1mg.com/articles/7-amazing-ways-pudina-mint-can-improve-your-health/",
        "Basella Alba (Basale)": "http://ccras.nic.in/content/less-known-facts-about-health-benefits-basella-alba",
        "Azadirachta Indica (Neem)": "https://www.1mg.com/ayurveda/neem-15?wpsrc=Google+Organic+Search"
    }

    url = urls.get(class_label)
    if not url:
        return ["Plant not found."]

    response = requests.get(url)
    if response.status_code != 200:
        return [f"Failed to fetch plant information from the website. Status code: {response.status_code}"]

    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find('body')  # Fetch content from the body of the page as a fallback

    # Check specific structure if known
    if class_label == "Syzygium Cumini (Jamun)":
        content = soup.find('div', class_='abstract-content selected')
    elif class_label == "Ocimum Tenuiflorum (Tulsi)":
        content = soup.find('div',class_="TextComponent__text___wvzbD")
    elif class_label == "Citrus Limon (Lemon)":
        if class_label == "Citrus Limon (Lemon)" and content:
            paragraphs = content.find_all('p')
            first_two_paragraphs = paragraphs[:6]
            first_two_paragraphs_text = [paragraph.get_text().strip() for paragraph in first_two_paragraphs]
            return first_two_paragraphs_text        
        #content = soup.find('p', class_='gt-block')
        

    elif class_label == "Brassica Juncea (Indian Mustard)":
        content = soup.find('div', class_='content')
    elif class_label == "Psidium Guajava (Guava)":
        content = soup.find('div',class_='css-1avyp1d')
    elif class_label == "Punica Granatum (Pomegranate)":
        content = soup.find('div',class_="report-content")
    elif class_label == "Mangifera Indica (Mango)":
        content = soup.find('div', class_='section-wrapper shadow-none article-body')
    elif class_label == "Mentha (Mint)":
        content=soup.find('div',class_='entry-content clearfix')
    elif class_label == "Basella Alba (Basale)":
        content = soup.find('div', class_='field-item even')
    elif class_label == "Azadirachta Indica (Neem)":
        content = soup.find('div', class_='TextComponent__text___wvzbD')

    if content:
        return [content.text.strip()]

    return ["No specific content found or the page does not contain relevant information."]

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            class_label, confidence = classify_image(filename)
            details = scrape_details(class_label)
            return render_template('result.html', class_label=class_label, confidence=confidence, details=details, img_path=url_for('uploaded_file', filename=file.filename))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
