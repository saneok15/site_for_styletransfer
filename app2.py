from flask import render_template, request, Response, redirect, url_for, g, session
from werkzeug.utils import secure_filename
import os
import redis
from rq import Queue
from app.send_to_worker import background_task
import asyncio
import time
import pymongo
from PIL import Image
import gridfs
from app import app
import datetime


with open('p/mongo') as f:
    mongo_login = f.readline()
    print(mongo_login)

client = pymongo.MongoClient(mongo_login)
db = client['diplom_images']
collection = db['diplom_images']
fs = gridfs.GridFS(db)
app.debug = True
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = 'static/cached_img'

r = redis.Redis()
q = Queue(connection=r)

@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        if request.form['submitter'] == 'Почати обробку':

            target = request.files['target']
            style = request.files['style']
            print(('target' in request.files), ('style' in request.files) )


            try:
                target_im = Image.open(target)
                loaddatetime_target = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                #print(loaddatetime_target)
                #print(secure_filename(target.filename))
                target_filename = loaddatetime_target + secure_filename(target.filename)

            except IOError:
                return render_template("index.html", success = 'Завантажте обидва зображення',submitbutton = '1', targetinput = '1',styleinput = '1')

            try:
                style_im = Image.open(style)
                loaddatetime_style = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                style_filename = loaddatetime_style + secure_filename(style.filename)

            except IOError:
                return render_template("index.html", success = 'Завантажте обидва зображення',submitbutton = '1', targetinput = '1',styleinput = '1')


            total_target_filename = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)
            target_im.save(total_target_filename)

            style_target_filename = os.path.join(app.config['UPLOAD_FOLDER'], style_filename)
            style_im.save(style_target_filename)
            print('saved')

            start = time.time()
            print(start)

            job = q.enqueue(background_task, [total_target_filename,style_target_filename],job_timeout=600)

            while job.result == None:
                time.sleep(1)
    #
            print(job.result)

    
            total_time = time.time() - start
            print(total_time)
            result = str(job.result)


            return render_template("index.html", resultfilename= result ,stylefilename=style_filename, targetfilename=target_filename, tryagainbutton = '1')
        if request.form['submitter'] == 'Спробувати знову':
            return render_template("index.html", submitbutton='1', targetinput='1', styleinput='1')

    else:
        return render_template("index.html", submitbutton = '1', targetinput = '1',styleinput = '1')

@app.route('/display/<filename>')
def display_image(filename):
	print('display_image filename: ' + filename)
	return redirect(url_for('static', filename= 'cached_img/'+filename), code=301)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=False)