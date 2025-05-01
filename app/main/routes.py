# app/main/routes.py
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.main import bp
import os
import uuid
from azure.storage.blob import BlobServiceClient
import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def upload_to_azure(file_path, filename):
    try:
        # Get connection string from app config
        connect_str = current_app.config['AZURE_STORAGE_CONNECTION_STRING']
        container_name = current_app.config['AZURE_CONTAINER_NAME']
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        
        # Generate a unique name for the blob
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create a blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=unique_filename
        )
        
        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)
            
        # Return the URL for the blob
        return blob_client.url
    except Exception as e:
        print(f"Azure upload error: {str(e)}")
        return None

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Upload to Azure Blob Storage
        azure_url = upload_to_azure(file_path, filename)
        
        if azure_url:
            return render_template('uploaded.html', filename=filename, azure_url=azure_url)
        else:
            flash('Failed to upload to Azure')
            return redirect(url_for('main.index'))
    else:
        flash('File type not allowed')
        return redirect(url_for('main.index'))