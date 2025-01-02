from flask import Flask, request, redirect, url_for, render_template
import requests
import time
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
API_KEY = "cm13mpgl20007mh03348pu3wy"
UPLOAD_URL = "https://api.magicapi.dev/api/v1/capix/faceswap/faceswap/v1/video"
FILE_UPLOAD_URL = "https://api.magicapi.dev/api/v1/capix/faceswap/upload/"
RESULT_URL = "https://api.magicapi.dev/api/v1/capix/faceswap/result/"

@app.route('/')
def upload_form():
    return render_template('index.html', video_url="https://cdn.pixabay.com/video/2025/01/01/249977.mp4")

@app.route('/videosettings', methods=['POST'])
def choose_character():
    target_url = request.form.get('target_url')
    swap_file = request.files.get('swap_file')
    swap_url = upload_file_to_url(swap_file)
    return render_template('submit_settings.html', target_url=target_url, swap_url=swap_url, target_face_index=0)

@app.route('/swap', methods=['POST'])
def face_swap():
    target_url = request.form.get('target_url')
    swap_url = request.form.get('swap_url')
    target_face_index = request.form.get('target_face_index', 0)
    if not swap_url:
        print("Missing files: target_file or swap_file is not provided.!!!!")
    if not target_url:
        print("Missing files: target_file or swap_file is not provided.!!!!@@@@@")
    if not target_url or not swap_url:
        print("Missing files: target_file or swap_file is not provided.")
        return 'Both target_file and swap_file are required.'

    payload = {
        'target_url': target_url,
        'swap_url': swap_url,
        'target_face_index': target_face_index
    }

    headers = {
        'x-magicapi-key': API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json'
    }

    response = requests.post(UPLOAD_URL, data=payload, headers=headers)

    print(f"Face swap API response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        json_response = response.json()

        request_id = json_response.get('image_process_response', {}).get('request_id')

        if request_id:
            print(f"Request ID received: {request_id}")
            return redirect(url_for('check_result', request_id=request_id))
        else:
            print("Failed to get request_id from the API response.")
            return 'Failed to get request_id from the API response.'
    else:
        return f'Failed! Status Code: {response.status_code}, Response: {response.text}'

@app.route('/result/<request_id>')
def check_result(request_id):
    payload = {
        'request_id': request_id
    }

    headers = {
        'x-magicapi-key': API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json'
    }

    max_attempts = 10  # Maximum number of polling attempts
    poll_interval = 2  # Time (in seconds) between each polling attempt

    for attempt in range(max_attempts):
        response = requests.post(RESULT_URL, data=payload, headers=headers)
        print(f"Attempt {attempt + 1}: Result API response: {response.status_code}, {response.text}")

        if response.status_code == 200:
            result_response = response.json()
            status = result_response.get('image_process_response', {}).get('status')
            if status == "OK":
                result_url = result_response.get('image_process_response', {}).get('result_url')
                if result_url:
                    print(f"Result URL received: {result_url}")
                    return render_template('index.html', video_url=result_url)
                else:
                    print("Failed to get result_url from the API response.")
                    return 'Failed to get result_url from the API response.'
            elif status == "InProgress":
                print("The task is still in progress. Retrying...")
                time.sleep(poll_interval)  # Wait before the next attempt
            else:
                print(f"Unexpected status: {result_response}")
                return f'Unexpected status: {result_response}'
        else:
            print(f"Failed API call with status code: {response.status_code}")
            time.sleep(poll_interval)  # Wait before the next attempt

    print("Maximum polling attempts reached. Task may still be in progress.")
    return 'The task is still in progress. Please wait and try again later.'


def upload_file_to_url(file):
    files = {'file1': (file.filename, file, file.content_type)}
    headers = {
        'x-magicapi-key': API_KEY,
        'accept': 'application/json'
    }

    print(f"Uploading file: {file.filename}, Content-Type: {file.content_type}")
    
    response = requests.post(FILE_UPLOAD_URL, files=files, headers=headers)

    print(f"File upload response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        json_response = response.json()
        upload_url = json_response.get('result')  # Corrected to match the API response
        if upload_url:
            print(f"File uploaded successfully. URL: {upload_url}")
        else:
            print(response)
            print("File upload successful but no URL received in response.")
        return upload_url
    else:
        print("File upload failed.")
        return None

if __name__ == '__main__':
    app.run(debug=True)

