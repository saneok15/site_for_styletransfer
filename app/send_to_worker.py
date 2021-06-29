import asyncio
from flask import Flask, render_template, request, redirect
import websockets
import pickle
import pymongo
import gridfs
from PIL import Image

with open('p/mongo') as f:
    mongo_login = f.readline()
client = pymongo.MongoClient(mongo_login)
db = client['diplom_images']
collection = db['diplom_images']
fs = gridfs.GridFS(db)
ip_list = []
with open('p/adress') as f:
    for line in f:
        ip_list.append('ws://'+line)
#uri = "ws://localhost:8765"
print(ip_list)

async def background_task(links):


    try:
        with open(links[0], 'rb') as f:
            target_im_b = f.read()
            print('read')
    except:
        print(links[0]+' not found')


    try:
        with open(links[1], 'rb') as f:
            style_im_b = f.read()
            print('read')
    except:
        print(links[1] + ' not found')

    try:
        target = fs.put(target_im_b, filename=links[0])
        print('put')
    except:
        print('smth gone wrong')

    try:
        target_mongo_id =fs.get(target)._id
        print(target_mongo_id)
    except:
        print('smth gone wrong')

    try:
        style = fs.put(style_im_b, filename=links[1])
        print('put')
    except:
        print('smth gone wrong')

    try:
        style_mongo_id = fs.get(style)._id
        print(style_mongo_id)
    except:
        print('smth gone wrong')

    img_ids = [target_mongo_id,style_mongo_id]
    async with websockets.connect(ip_list[0],ping_interval=None) as websocket:
        data = pickle.dumps(img_ids)
        await websocket.send(data)


        result_mongo_dump_id = await websocket.recv()
        result_mongo_id = pickle.loads(result_mongo_dump_id)
        result_img = fs.get(result_mongo_id[0])
        print(result_img,result_img.filename)

        result_filename = str(result_img.filename)[5:]
        result_filename_to_save = 'static/cached_img/'+str(result_img.filename)[5:]
        Image.open(result_img).save(result_filename_to_save, 'PNG')

        print(result_filename)

    print("Task complete")
    return result_filename
