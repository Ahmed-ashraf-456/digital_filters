import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import (Flask, json, jsonify, redirect, render_template, request,
                   url_for)
from flask.wrappers import Response
from numpy import lib
from numpy.core.records import array
from numpy.matrixlib import defmatrix
from scipy import signal

i = 0
zeros = []
poles = []
gain = 1
b = []
a = []
allpassfiltersreal = []
allpassfiltersimg = []
allpassfilterszeros = []
allpassfilterspoles = []
w = []
h = []
originalData = []
magnitudeplotdata = []
angleplotdata = []
filteredSignalYdata = []
library = []
path = ""


def getMyData():
    global signalData, signalxAxisData, signalyAxisData, dataLength
    signalData = pd.read_csv(path)
    signalxAxisData = signalData.values[:, 0]
    signalyAxisData = signalData.values[:, 1]
    dataLength = len(signalxAxisData)


def maplibrary(x, y):
    return str(str(x) + "+" + str(y) + "j")


def readlibrary():
    global allpassfiltersreal, allpassfiltersimg, library
    data = pd.read_csv(r'library.csv')
    allpassfiltersreal = data.values[:, 0]
    allpassfiltersimg = data.values[:, 1]
    library = list(map(maplibrary, allpassfiltersreal, allpassfiltersimg))


def writeliberary():
    global allpassfiltersreal, allpassfiltersimg
    df = pd.DataFrame(allpassfiltersimg, allpassfiltersreal)
    df.to_csv('library.csv')


def makefilter():
    # w is the omega or the x axis of the magnitude and frequency responsevalues
    # h is an array that hold two array one is the magnitude and one is the phase
    global w, h
    w, h = signal.freqz_zpk(zeros, poles, gain)



def getfrequencyresponse():
    global magnitudeplotdata, angleplotdata
    magnitudeplotdata = 20 * np.log10(abs(h))
    angleplotdata = np.unwrap(np.angle(h))
    magnitudeplotdata = np.around(magnitudeplotdata, 4)



def allpassfiltermaker():
    global zeros, poles, magnitudeplotdata
    makefilter()
    getfrequencyresponse()
    zeros = np.array(
        [[np.real(zeros[0]) * 100 + 150,
          np.imag(zeros[0]) * (-100) + 150]])
    poles = np.array(
        [[np.real(poles[0]) * 100 + 150,
          np.imag(poles[0]) * (-100) + 150]])

    return {
        'library': library,
        'zeros': zeros.tolist(),
        'poles': poles.tolist(),
        'w': w.tolist(),
        'magnitude': magnitudeplotdata.tolist(),
        'angle': angleplotdata.tolist()
    }




def filterdata(originalData):
    global b, a, filteredSignalYdata
    b, a = signal.zpk2tf(zeros, poles, gain)
    filteredSignalYdata = np.real(signal.lfilter(b, a, originalData))
    return filteredSignalYdata




def format(x):
    return (x[0] + 1j * x[1])



def frequencyrespose():
    makefilter()
    getfrequencyresponse()
    return {
        'w': w.tolist(),
        'magnitude': magnitudeplotdata.tolist(),
        'angle': angleplotdata.tolist()
    }



def formattocoardinates(x):
    return ([np.real(x) * 100 + 150, np.imag(x) * (-100) + 150])


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/getzeros', methods=['POST', 'GET'])
def getzeros():
    global zeros
    if request.method == 'POST':
        zeros = json.loads(request.data)
        return jsonify(zeros)
    return render_template("index.html")



@app.route('/generate', methods=['POST'])
def last():
    if request.method == 'POST':
        value = request.json['signal']
        value = np.array(value)
        value = filterdata(value) 
        print(value)
        return json.dumps(value.tolist())
    return render_template("index.html")

    
@app.route('/getpoles', methods=['POST', 'GET'])
def getpoles():
    if request.method == 'POST':
        global poles
        data = request.data
        data = json.loads(data)
        poles = data
        return jsonify(data)
    return render_template("index.html")


@app.route('/getallpassfilter', methods=['POST', 'GET'])
def getallpassfilter():
    if request.method == 'POST':
        global i, zeros, poles
        data = json.loads(request.data)
        if (type(data) == str):
            i = int(data)
            temp = allpassfiltersreal[i] + 1j * allpassfiltersimg[i]
            zeros = [1 / np.conjugate(temp)]
            poles = [temp]
        else:
            temp = data[0] + 1j * data[1]
            zeros = [1 / np.conjugate(temp)]
            poles = [temp]
        return jsonify(0)
    return render_template("index.html")


@app.route('/sendallpassfilter', methods=['POST', 'GET'])
def sendallpassfilter():
    if request.method == 'GET':
        temp = allpassfiltermaker()
        return jsonify(temp)
    return render_template("index.html")


@app.route('/updatelibrary', methods=['POST', 'GET'])
def updatelibrary():
    global allpassfiltersimg, allpassfiltersreal
    if request.method == 'GET':
        readlibrary()
        return jsonify(library)
    if request.method == 'POST':
        data = json.loads(request.data)
        allpassfiltersreal = np.append(allpassfiltersreal, data[0])
        allpassfiltersimg = np.append(allpassfiltersimg, data[1])
        writeliberary()
        readlibrary()
        return jsonify(library)
    return render_template("index.html")


@app.route('/sendfrequencyresposedata', methods=['POST', 'GET'])
def senddata():
    global zeros, poles
    if request.method == 'GET':
        print(zeros)
        zeros = list(map(format, zeros))
        poles = list(map(format, poles))
        zeros = [*zeros, *allpassfilterszeros]
        poles = [*poles, *allpassfilterspoles]
        temp = frequencyrespose()
        return jsonify(temp)
    return render_template("index.html")


@app.route('/activateordeactivateallpassfilter', methods=['POST', 'GET'])
def activateordeactivateallpassfilter():
    global allpassfilterszeros, allpassfilterspoles, zeros, poles
    if request.method == 'POST':
        data = int(json.loads(request.data))
        a = float(
            allpassfiltersreal[data]) + float(allpassfiltersimg[data]) * 1j
        tempzeros = 1 / np.conjugate(a)
        temppoles = a
        if tempzeros in allpassfilterszeros:
            allpassfilterszeros.remove(tempzeros)
        else:
            allpassfilterszeros.append(tempzeros)
        if temppoles in allpassfilterspoles:
            allpassfilterspoles.remove(temppoles)
        else:
            allpassfilterspoles.append(temppoles)
        tempzeros = list(map(formattocoardinates, allpassfilterszeros))
        temppoles = list(map(formattocoardinates, allpassfilterspoles))
        return jsonify({
            'allpassfilterzeros': tempzeros,
            'allpassfilterpoles': temppoles
        })
    return render_template("index.html")


@app.route('/getSignals', methods=['POST', 'GET'])
def dataFilter():
    global b, a
    if request.method == 'POST':
        arr = json.loads(request.data)
        i = int(arr[0])
        size = int(arr[1])
        print(size)
        print("ahmed ashraf")
        x_chuncks = np.array(signalxAxisData[i * size:(i + 1) * size])
        y_chuncks = np.array(signalyAxisData[i * size:(i + 1) * size])
        filterdata(y_chuncks)
        return jsonify({
            'xAxisData': x_chuncks.tolist(),
            'yAxisData': y_chuncks.tolist(),
            'filter': filteredSignalYdata.tolist(),
            'datalength': dataLength,
        })
    return render_template("index.html")


@app.route('/getData', methods=['POST'])
def my_form_post():
    global path
    if request.method == 'POST':
        path = json.loads(request.data)
        getMyData()
        return jsonify(path)
    return render_template("index.html")





if __name__ == '__main__':
    app.run(debug = True)
