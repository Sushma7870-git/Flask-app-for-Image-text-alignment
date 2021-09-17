import os
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import numpy as np
import cv2

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        angle=check_skew(os.path.join(app.config['UPLOAD_FOLDER'],filename))
		#print('upload_image filename: ' + filename)
        # flash('Image successfully uploaded and displayed below')
        
        if angle==0:
            flash("Image is correctly alligned")

        return render_template('upload.html', filename=filename,angle=angle)
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)

@app.route('/displasy/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

def check_skew(image):
    # load the image from disk
    image = cv2.imread(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    thresh = cv2.threshold(gray, 0, 255,
    cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    #print('coords',coords)
    angle = cv2.minAreaRect(coords)[-1]
    #print('angle',angle)
    return angle

@app.route('/deskew', methods=['POST'])
def deskew():
    filename=request.form.get('filename')
    angle=request.form.get('angle')
    angle=float(angle)
    if angle < -45:
       angle = -(90 + angle)
    else:
        angle = -angle
    image_path=os.path.join(app.config['UPLOAD_FOLDER'],filename)
    image = cv2.imread(image_path)

    #print('image path',image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255,
    cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # rotate the image to deskew it
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    new_filename=filename.split('.')[0]+"-deskew.jpeg"
    cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], new_filename),rotated)
    
    return render_template('deskew.html', filename=new_filename,angle=angle)

if __name__ == "__main__":
    app.run()
    # print('working')