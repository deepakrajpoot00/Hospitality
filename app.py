from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
import pandas as pd
from collections import defaultdict
from flask import send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

# Home route for index page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        group_file = request.files['group_file']
        hostel_file = request.files['hostel_file']
        
        if group_file.filename == '' or hostel_file.filename == '':
            return redirect(request.url)
        
        # Save uploaded files
        group_file_path = os.path.join(app.config['UPLOAD_FOLDER'], group_file.filename)
        hostel_file_path = os.path.join(app.config['UPLOAD_FOLDER'], hostel_file.filename)
        group_file.save(group_file_path)
        hostel_file.save(hostel_file_path)
        
        # Process files
        group_allocation, output_path = process_files(group_file_path, hostel_file_path)
        
        return render_template('result.html', group_allocation=group_allocation, output_path=output_path)
    
    return render_template('index.html')

# Function to process CSV files and allocate rooms
def process_files(group_file, hostel_file):
    # Read group information
    group_df = pd.read_csv(group_file)
    
    # Read hostel information
    hostel_df = pd.read_csv(hostel_file)
    
    # Initialize data structures
    group_allocation = defaultdict(list)
    allocation_details = []

    # Group by Group ID and process allocation
    for idx, group_row in group_df.iterrows():
        group_id = group_row['Group ID']
        members = group_row['Members']
        gender = group_row['Gender']
        
        # Filter hostels by gender
        suitable_hostels = hostel_df[hostel_df['Gender'] == gender]
        
        # Sort hostels by remaining capacity
        suitable_hostels = suitable_hostels.sort_values(by='Capacity', ascending=False)
        
        allocated = False
        for h_idx, hostel_row in suitable_hostels.iterrows():
            room_number = hostel_row['Room Number']
            capacity = hostel_row['Capacity']
            
            if capacity >= members:
                group_allocation[group_id].append((hostel_row['Hostel Name'], room_number, members))
                allocation_details.append((group_id, hostel_row['Hostel Name'], room_number, members))
                allocated = True
                break
        
        if not allocated:
            allocation_details.append((group_id, 'Unallocated', '', members))

    # Prepare output for CSV download
    output_filename = 'allocation_details.csv'
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Group ID', 'Hostel Name', 'Room Number', 'Members Allocated'])
        for allocation in allocation_details:
            writer.writerow(allocation)
    
    return group_allocation, output_path

# Route for downloading allocation details
@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
