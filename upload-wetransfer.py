#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Upload files or folder WeTransfer
#
# VERSION       :1.0
# DATE          :2014-12-27
# AUTHOR        :Kevin Raynel <https://github.com/kraynel>
# URL           :https://github.com/kraynel/upload-wetransfer
# DEPENDS       :pip install requests,requests-toolbelt

from urlparse import urlparse, parse_qs
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

import os, requests, sys, json, re, argparse, sys, mimetypes, collections

WE_TRANSFER_API_URL = "https://www.wetransfer.com/api/v1/transfers"
CHUNK_SIZE = 5242880

def getTransferId(sender, receivers, message):
    dataTransferId =  { "channel":"", 
    "expire_in":   "",
    "from":    sender,
    "message": message,
    "pw" : "",
    "to[]" :   receivers,
    "ttype" :  "1",
    "utype" :  "js"
    }

    r = requests.post(WE_TRANSFER_API_URL, data=dataTransferId)
    response_data = json.loads(r.content)

    return response_data["transfer_id"]

def getFileObjectId(transferId, filename, filesize):
    dataFileObjectId =  { "chunked": "true", 
    "direct":   "false",
    "filename":    filename,
    "filesize": filesize
    }

    r = requests.post((WE_TRANSFER_API_URL + "/{0}/file_objects").format(transferId), data=dataFileObjectId)
    response_data = json.loads(r.content)

    return response_data


def getChunkInfoForUpload(transferId, fileObjectId, chunkNumber, chunkSize=CHUNK_SIZE):
    dataChunk = { "chunkNumber" : chunkNumber,
    "chunkSize" :  chunkSize,
    "retries" : "0" }

    r = requests.put((WE_TRANSFER_API_URL + "/{0}/file_objects/{1}").format(transferId, fileObjectId), data=dataChunk)
    
    return json.loads(r.content)

def drawProgressBar(percent, barLen = 20):
    sys.stdout.write("\r")
    progress = ""
    for i in range(barLen):
        if i < int(barLen * percent):
            progress += "="
        else:
            progress += " "
    sys.stdout.write("[ %s ] %.2f%%" % (progress, percent * 100))
    sys.stdout.flush()

def uploadChunk(chunkInfo, filename, dataBin, fileType, chunkNumber, fileSize):
    url = chunkInfo["url"]
    
    dataChunkUpload = collections.OrderedDict()
    for k, v in chunkInfo["fields"].items():
        dataChunkUpload[k] = v

    dataChunkUpload["file"] = (filename, dataBin, fileType)
    r = requests.post(url, files=dataChunkUpload)
    print (chunkNumber * CHUNK_SIZE / fileSize)
    #drawProgressBar(chunkNumber * CHUNK_SIZE / fileSize)

def finalizeChunks(transferId, fileObjectId, partCount):
    print("Finalize file/chunk : ")
    dataFinalizeChunk = {
    "finalize_chunked"  : "true",
    "part_count"  : partCount
    }

    r = requests.put((WE_TRANSFER_API_URL + "/{0}/file_objects/{1}").format(transferId, fileObjectId), data=dataFinalizeChunk)
    #print(r.text)

def finalizeTransfer(transferId):
    print("Finalize transfer")
    
    r = requests.put((WE_TRANSFER_API_URL + "/{0}/finalize").format(transferId))
    print(r.text)
    
def read_in_chunks(file_object, chunk_size=CHUNK_SIZE):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 5Mo."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def uploadFile(transferId, fileToUpload):
    with open(fileToUpload, 'rb') as f:
        fileMimeType = "application/octet-stream" 
        #mimetypes.read_mime_types(f.name)
        fileSize = os.path.getsize(fileToUpload)
        fileName = os.path.basename(fileToUpload)

        dataFileObjectId = getFileObjectId(transferId, fileName, fileSize)
        if dataFileObjectId.has_key("url"):
            uploadChunk(dataFileObjectId, fileName, f.read(fileSize), fileMimeType)
            finalizeChunks(transferId, dataFileObjectId["file_object_id"], 1)
        else:
            chunkNumber = 1
            print("Upload file : " + fileName)
    
            for piece in read_in_chunks(f):
                chunkInfo = getChunkInfoForUpload(transferId, dataFileObjectId["file_object_id"], chunkNumber, sys.getsizeof(piece))
                uploadChunk(chunkInfo, fileName, piece, fileMimeType, chunkNumber, fileSize)
                chunkNumber = chunkNumber + 1

            finalizeChunks(transferId, dataFileObjectId["file_object_id"], chunkNumber - 1)

def uploadDir(top, transferId, recursive):
    '''descend the directory tree rooted at top,
       calling the upload function for each regular file'''

    for root, dirs, files in os.walk(top):
        if not recursive:  
            while len(dirs) > 0:  
                dirs.pop()  
        
        for name in files:
            print("Upload file : " + os.path.abspath(os.path.join(root, name)))
            uploadFile(transferId, os.path.abspath(os.path.join(root, name)))

def main(argv):
    parser = argparse.ArgumentParser(description='Uploads files or folders to WeTransfer.')
    parser.add_argument('-r', '--receiver', help='emails of the receivers', nargs='*')
    parser.add_argument('-s', '--sender', help='email of the sender', default="myEmail@myDomain.com")
    parser.add_argument('-m', '--message', help='message to send')
    parser.add_argument('-R', '--recursive', help='recursive send', action='store_true')
    parser.add_argument('files', help='files or directory to send', nargs='+')
    
    args = parser.parse_args();
    mimetypes.init()

    transferId = getTransferId(args.sender, args.receiver, args.message)
    
    for it in args.files:
        if os.path.isfile(it):
            print("Upload file : " + it)
            uploadFile(transferId, files)
        elif os.path.isdir(it):
            uploadDir(it, transferId, args.recursive)
        else:
            print("Not a file/directory : " + it)
            
    
    finalizeTransfer(transferId)

if __name__ == "__main__":
    main(sys.argv[1:])
