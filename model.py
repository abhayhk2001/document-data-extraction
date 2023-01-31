import torch
from pdf2image import convert_from_path
import os
import shutil
import pytesseract
from PIL import Image
import argparse


parser = argparse.ArgumentParser(description='run invoice detection')
parser.add_argument('--file', help='enter path of invoice')
args = parser.parse_args()

poppler_path = r'poppler-22.04.0/Library/bin'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

with open('results.txt', 'w') as f:
    f.truncate(0)

save_dir = 'runs/detect'


def set_dir(invoice_path):
    invoice_name = invoice_path.split('\\')[-1]

    company_dir = os.path.join('runs/detect/exp/crops/COMPANY', invoice_name)
    invoice_date_dir = os.path.join(
        'runs/detect/exp/crops/INVOICE DATE', invoice_name)
    table_dir = os.path.join('runs/detect/exp/crops/TABLE', invoice_name)
    total_dir = os.path.join('runs/detect/exp/crops/TOTAL', invoice_name)
    gst_dir = os.path.join('runs/detect/exp/crops/GST', invoice_name)
    abn_dir = os.path.join('runs/detect/exp/crops/ABN', invoice_name)
    account_dir = os.path.join(
        'runs/detect/exp/crops/ACCOUNT_DETAILS', invoice_name)

    crop_img_paths = [{'field': 'company', 'path': company_dir}, {'field': 'invoice date', 'path': invoice_date_dir}, {'field': 'Total', 'path': total_dir}, {
        'field': 'gst', 'path': gst_dir}, {'field': 'abn', 'path': abn_dir}, {'field': 'Account Details', 'path': account_dir}]
    return crop_img_paths, table_dir


os.chmod(save_dir, 0o777)


def clear_directory(save_dir):
    for f in os.listdir(save_dir):
        shutil.rmtree(os.path.join(save_dir, f))


def predict(model, image):
    results = model(image)
    crops = results.crop()
    # print(results.pandas().xyxy[0])


def retrieve_text(field_name, image_path):
    # print(field_name,image_path)
    try:
        img = Image.open(image_path)
        img_text = pytesseract.image_to_string(img, lang='eng_layer')
        print(field_name + ':' + img_text)
        with open('results.txt', 'a') as f:
            f.writelines(field_name + ':' + img_text)
            f.close()
    except Exception as e:
        # print(e)
        print(field_name + ' not found')


def main():
    clear_directory(save_dir)
    model = torch.hub.load('ultralytics/yolov5',
                           'custom', path='weights/best.pt')
    invoice_path = args.file
    invoice = invoice_path
    # path to image
    img_supp_types = '.jpg' or '.png'
    if invoice.endswith(img_supp_types):
        predict(model, invoice_path)
        crop_img_paths, table_dir = set_dir(invoice)
        for img in crop_img_paths:
            # print(img)
            retrieve_text(img['field'], img['path'])
        print('TABLE DETAILS:')
        table_path = table_dir
        os.system(
            'python table-extraction\\table_transformer.py --table-type borderless -i ' + table_path)
        #print(crop_img_paths, table_dir)
    elif invoice.endswith('.pdf'):
        path_split = os.path.split(invoice)
        temp_fol = os.path.join(path_split[0], 'temp')
        exp_fol = os.path.join(temp_fol, path_split[1][:-4])
        shutil.rmtree(temp_fol)
        os.makedirs(exp_fol)
        images = convert_from_path(
            invoice, 500, exp_fol, fmt='jpeg', poppler_path=poppler_path)
        # print(images)
        for imag in os.scandir(exp_fol):
            clear_directory(save_dir)
            imag_path = imag.path
            imag_name = imag.name
            # print(str(imag_name))
            predict(model, imag_path)
            crop_img_paths, table_dir = set_dir(imag_path)
            for img in crop_img_paths:
                retrieve_text(img['field'], img['path'])
            print('TABLE DETAILS:')

            table_path = imag_path
            os.system(
                'python table-extraction\\table_transformer.py --table-type bordered -i ' + table_path)


if __name__ == "__main__":
    main()

# !python3 table_transformer.py --table-type borderless -i "/content/open-intelligence-backend/datasets/all_tables/2.png"
