# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from PySide import QtGui
import math
import re
import sys
import pandas as pd
from collections import OrderedDict
import spotlight
from nltk.tokenize import word_tokenize
import json, ast
import xlrd
from urllib2 import urlopen
from contextlib import closing

reload(sys)
sys.setdefaultencoding('utf-8')
from PyQt4 import QtGui
from PyQt4.QtGui import *
import math
import re
import sys
import json, ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pylab import *
from PyQt4 import QtGui, QtCore
import goslate
import tweepy
from PyQt4 import QtGui, QtCore
import json, ast
import pandas as pd
from PyQt4.QtCore import Qt
from PyQt4.QtGui import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QFrame, QGridLayout, QVBoxLayout,
)
from PyQt4.QtCore import *

reload(sys)
sys.setdefaultencoding('utf-8')

# AFINN-111 is as of June 2011 the most recent version of AFINN
filenameAFINN = 'AFINN/AFINN-111.txt'
afinn = dict(map(lambda (w, s): (w, int(s)), [
    ws.strip().split('\t') for ws in open(filenameAFINN)]))

# Word splitter pattern
pattern_split = re.compile(r"\W+")


def sentiment(text):
    """
    Returns a float for sentiment strength based on the input text.
    Positive values are positive valence, negative value are negative valence.
    """
    words = pattern_split.split(text.lower())
    sentiments = map(lambda word: afinn.get(word, 0), words)
    if sentiments:
        # How should you weight the individual word sentiments?
        # You could do N, sqrt(N) or 1 for example. Here I use sqrt(N)
        sentiment = float(sum(sentiments)) / math.sqrt(len(sentiments))

    else:
        sentiment = 0
    return sentiment


class MyHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, theme):
        QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        PROHIBITED_keyword = QTextCharFormat()
        NSA_keyword = QTextCharFormat()
        DHS_keyword = QTextCharFormat()
        self.highlightingRules = []

        # PROHIBITED_keyword
        brush = QBrush(Qt.green, Qt.SolidPattern)
        PROHIBITED_keyword.setForeground(brush)
        PROHIBITED_keyword.setFontWeight(QFont.Bold)
        keywords = QStringList([line.rstrip('\n') for line in open('PROHIBITED.txt')])
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, PROHIBITED_keyword)
            self.highlightingRules.append(rule)

        # NSA_keyword
        brush = QBrush(Qt.red, Qt.SolidPattern)
        NSA_keyword.setForeground(brush)
        NSA_keyword.setFontWeight(QFont.Bold)
        keywords = QStringList([line.rstrip('\n') for line in open('NSA.txt')])
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, NSA_keyword)
            self.highlightingRules.append(rule)

        # DHS_pedia_keyword
        brush = QBrush(Qt.blue, Qt.SolidPattern)
        DHS_keyword.setForeground(brush)
        DHS_keyword.setFontWeight(QFont.Bold)
        keywords = QStringList([line.rstrip('\n') for line in open('DHS.txt')])
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, DHS_keyword)
            self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = text.indexOf(expression, index + length)
        self.setCurrentBlockState(0)


class HighlightingRule():
    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.form_widget = MyTweet(self)
        _widget = QtGui.QWidget()
        _layout = QtGui.QVBoxLayout(_widget)
        _layout.addWidget(self.form_widget)
        self.setCentralWidget(_widget)


class MyTweet(QtGui.QMainWindow):
    def __init__(self, parent):
        super(MyTweet, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.initUI()

    def initUI(self):
        # self.setGeometry(200, 100, 750, 50)
        self.frame = QFrame(self)

        box = QtGui.QHBoxLayout()
        # self.frame.setFrameShape(QFrame.Box)
        grid = QGridLayout(self.frame)
        label = QLabel('Your Tweet      ', self.frame)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        font = QFont()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.textedit = QTextEdit(self.frame)
        self.textedit.setToolTip('<b> Please enter your tweet here ... </b> ')
        self.textedit.installEventFilter(self)
        self.textedit.setMaximumHeight(label.sizeHint().height() * 4)
        self.textedit.setFont(font)
        highlighter = MyHighlighter(self.textedit, "Classic")

        grid.addWidget(label, 1, 0)
        grid.addWidget(self.textedit, 1, 1)
        grid.setContentsMargins(40, 10, 300, 500)
        qbtn1 = QtGui.QPushButton('Send', self)
        qbtn1.resize(qbtn1.sizeHint())
        qbtn1.move(460, 20)
        qbtn1.clicked.connect(self.sendPressed)
        box.addWidget(qbtn1)
        qbtn2 = QtGui.QPushButton('Cancel', self)
        qbtn2.resize(qbtn2.sizeHint())
        qbtn2.move(560, 20)
        qbtn2.clicked.connect(self.close)
        box.addWidget(qbtn2)

        self.frame2 = QFrame(self)
        # self.frame2.move(50, 150)
        self.frame2.setGeometry(50, 150, 250, 100)

        self.frame2.setFrameShape(QFrame.Box)
        lbl0 = QtGui.QLabel("Green Color ", self)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.green)
        lbl0.setPalette(palette)
        lbl0.move(60, 160)
        lbl1 = QtGui.QLabel("Inappropraite Words! ", self)
        lbl1.move(120, 160)
        lbl2 = QtGui.QLabel("Red Color ", self)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
        lbl2.setPalette(palette)
        lbl2.move(60, 185)
        lbl3 = QtGui.QLabel("NSA list! ", self)
        lbl3.move(110, 185)
        lbl4 = QtGui.QLabel("Blue Color ", self)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.blue)
        lbl4.setPalette(palette)
        lbl4.move(60, 210)
        lbl5 = QtGui.QLabel("DHS list!", self)
        lbl5.move(110, 210)

        self.statusBar().showMessage('Press Enter to see the Analysis of your Tweet ')
        self.frame.setLayout(grid)
        self.setCentralWidget(self.frame)
        self.setGeometry(50, 100, 750, 50)
        self.setWindowTitle('Tweet')
        self.show()

    def sendPressed(self):
        tweet = self.textedit.toPlainText()
        # print tweet
        # Mytable('6')

        CONSUMER_KEY = '90sGVaeiRyC5XfuiqANBh4WtW'
        CONSUMER_SECRET = '4zPmDOceet3L0H7p2f4yuqDCoymkHc2tCCvp5nwHDRtN9irTfM'
        ACCESS_KEY = '784829503776387072-FX3oLrY08w4zF7IYesu9zH17Gm8NQuU'
        ACCESS_SECRET = 'gRofpzGzUVC2IkoIPiFwHRAZbDbAHfgQeFNiYuLRF9l6M'

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

        api = tweepy.API(auth)
        # return tweet

        # self.k = "{0:.0f}%".format(100 * indicoio.sentiment(self.tweet))
        self.statusBar().showMessage('Sending... ')
        api.update_status(status=tweet)
        self.statusBar().showMessage('Your Tweet was send ')
        self.textedit.clear()
        # self.returnPressed(self)

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return:

                '''msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)

                msg.setText("This is a message box")
                msg.setInformativeText("This is additional information")
                msg.setWindowTitle("MessageBox demo")
                msg.setDetailedText("DETAIL")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)'''
                with open("mix.txt")as f:
                    file = [line.strip() for line in f]

                # textt = ''
                wordsss = self.textedit.toPlainText()
                wordss = str(wordsss).split()
                # print words
                l = 0
                kk = sentiment(str(wordsss))
                kh = float(kk)
                # print("%6.2f %s" % (sentiment(text), text))
                kh2 = (10) * ((float(kh) - (-5)) / (5 - (-5)))
                # print kh2
                list = [((0.25) * kh2)]
                for j in range(len(wordss)):
                    was = False
                    for i in range(len(file)):
                        if wordss[j] == file[i]:
                            print wordss[j]
                            # print("%6.2f %s" % (sentiment(words[j]), words[j]))
                            kh1 = float(sentiment(wordss[j]))
                            kh3 = (10) * ((float(kh1) - (-5)) / (5 - (-5)))
                            print kh3
                            l = l + 1
                            was = True

                            list.append(((0.25) * kh3) / 6)

                            # print l

                            # Automatically geolocate the connecting IP
                url = 'http://freegeoip.net/json/'
                try:
                    with closing(urlopen(url)) as response:
                        location = json.loads(response.read())
                        location_country = location['country_name']

                        print location_country
                        workbook = xlrd.open_workbook('HFI2.xlsx', "rb")
                        sheets = workbook.sheet_names()
                        required_data = []
                        required_data2 = []
                        for sheet_name in sheets:
                            sh = workbook.sheet_by_name(sheet_name)
                            for rownum in range(sh.nrows):
                                row_valaues = sh.row_values(rownum)
                                required_data.append((row_valaues[1], row_valaues[2]))
                                required_data2.append((row_valaues[1], row_valaues[4]))
                        m = ast.literal_eval(json.dumps(required_data))
                        m2 = ast.literal_eval(json.dumps(required_data2))
                        m.pop(0)
                        m2.pop(0)

                        mm = [i for n, (s, i) in enumerate(m) if s == location_country]
                        mmm = str(mm).strip('[]')
                        norm = (-10) * ((float(mmm) - 0) / 100) + 10
                        print float(mmm)
                        print float(norm)
                        list.append((0.25) * float(norm))

                        nn = [i for n, (s, i) in enumerate(m2) if s == location_country]
                        nnn = str(nn).strip('[]')

                        # print float(nnn)

                        list.append((0.25) * float(nnn))

                except:
                    print("error")

                annotations = spotlight.annotate('http://spotlight.sztaki.hu:2222/rest/annotate', str(wordsss))

                d = ast.literal_eval(json.dumps(annotations))
                # print d
                size = 2
                h = filter(
                    lambda person: person[
                                       # 'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person' or
                                       # person[
                                       'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person,DBpedia:Politician' or
                                   person[
                                       'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person,DBpedia:Politician,DBpedia:Senator' or
                                   person[
                                       'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person,DBpedia:OfficeHolder' or
                                   person[
                                       'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person,DBpedia:Politician,DBpedia:MemberOfParliament' or

                                   person[
                                       'types'] == 'DBpedia:Agent,Schema:Person,Http://xmlns.com/foaf/0.1/Person,DBpedia:Person,DBpedia:Politician,DBpedia:PrimeMinister',
                    d)
                m = []
                separator = ' , '
                for l in h:
                    # print l['surfaceForm']
                    # m = l['surfaceForm'] , l['URI']
                    # print m

                    # print("%6.2f %s" % (sentiment(l['surfaceForm']), l['surfaceForm']))
                    list.append(sentiment(l['surfaceForm']))
                    m.append(l['surfaceForm']), m.append(l['URI'])
                b = [m[i:i + size] for i in range(0, len(m), size)]
                print b
                b1 = [item[0] for item in b]
                b2 = [item[1] for item in b]
                #b3 = b2.linkActivated.connect(lambda link: openLink(link))
                print b1
                print b2
                b3 = str(separator.join(str(element) for element in b2))
                annotations1 = spotlight.annotate('http://spotlight.sztaki.hu:2222/rest/annotate', str(wordsss))

                d1 = ast.literal_eval(json.dumps(annotations1))
                # print d
                size = 2
                h1 = filter(
                    lambda place: place[
                                      'types'] == "Schema:Place,DBpedia:Place,DBpedia:PopulatedPlace,Schema:Country,DBpedia:Country",
                    d1)

                m1 = []

                for l1 in h1:
                    # print l['surfaceForm']
                    # m = l['surfaceForm'] , l['URI']
                    # print m



                    m1.append(l1['surfaceForm']), m1.append(l1['URI'])
                b4 = [m1[i:i + size] for i in range(0, len(m1), size)]
                b5 = [item[0] for item in b4]
                b9 = map(str.lower,b5)
                print b9

                b6 = []
                for x in b9:

                    if x != str(location_country.lower()):
                        b6.append(x)

                b7 = set(b6)

                b8 = str(separator.join(str(element) for element in b7))
                print b8

                # label.setOpenExternalLinks(True)  # opens your web browser
                with open("mix.txt")as f:
                    file1 = [line.strip() for line in f]

                # textt = ''
                wordsss1 = self.textedit.toPlainText()
                wordss1 = str(wordsss1).split()
                # print words
                l1 = 0
                kk1 = sentiment(str(wordsss1))
                kh1 = float(kk1)
                # print("%6.2f %s" % (sentiment(text), text))
                kh21 = (10) * ((float(kh1) - (-5)) / (5 - (-5)))
                # print kh2
                list1 = [((0.25) * kh21)]
                for j in range(len(wordss1)):
                    was = False
                    for i in range(len(file1)):
                        if wordss1[j] == file1[i]:
                            print wordss1[j]
                            # print("%6.2f %s" % (sentiment(words[j]), words[j]))
                            kh11 = float(sentiment(wordss1[j]))
                            kh31 = (10) * ((float(kh11) - (-5)) / (5 - (-5)))
                            print kh31
                            l1 = l1 + 1
                            was = True

                            list.append(((0.25) * kh31) / 6)

                            # print l

                            # Automatically geolocate the connecting IP
                       # print location_country
                workbook = xlrd.open_workbook('HFI2.xlsx', "rb")
                sheets = workbook.sheet_names()
                required_data11 = []
                required_data21 = []
                for sheet_name in sheets:
                    sh = workbook.sheet_by_name(sheet_name)
                    for rownum in range(sh.nrows):
                        row_valaues = sh.row_values(rownum)
                        required_data11.append((row_valaues[1], row_valaues[2]))
                        required_data21.append((row_valaues[1], row_valaues[4]))
                        m111 = ast.literal_eval(json.dumps(required_data11))
                        m2111 = ast.literal_eval(json.dumps(required_data21))
                        m111.pop(0)
                        m2111.pop(0)

                        mm1 = [i for n, (s, i) in enumerate(m111) if s == b8.capitalize()]
                        mmm1 = str(mm1).strip('[]')
                        #print mm1
                        #print mmm1
                        *norm1 = (-10) * ((float(mmm1) - 0) / 100) + 10
                        #print float(mmm)
                        #print float(norm)
                        *list.append((0.25) * float(norm1))

                        nn1 = [i for n, (s, i) in enumerate(m2111) if s == b8.capitalize()]
                        nnn1 = str(nn1).strip('[]')

                        # print float(nnn)

                        *list.append((0.25) * float(nnn1))





                #labels = ['Entity', 'URI']
                # print pd.DataFrame.from_records(b, columns=labels)
                # print list
                # print list.append(kk)

                text = (str(sum(list)))
                #print (str(sum(list)))
                text1 = (str(sum(list1)))
                #print (str(sum(list1)))
                # retval = msg.exec_()
                #Mytable(sum(list))
                # Mytable('6')

                table = QTableWidget()
                tableItem = QTableWidgetItem()


                # initiate table
                table.setWindowTitle("QTableWidget Example @pythonspot.com")
                table.resize(800, 200)
                table.setRowCount(2)
                table.setColumnCount(6)
                table.setAlternatingRowColors(True)
                table.setStyleSheet("alternate-background-color: lightgray; background-color: white;");
                table.setHorizontalHeaderLabels(QString("Country;High-Risk;Medium-Risk;Low-Risk;Entity;URI").split(";"))
                stylesheet1 = "QHeaderView::section{Background-color:rgb(190,1,1); border - radius:14px;}"
                table.setStyleSheet(stylesheet1)
                stylesheet = "::section{Background-color:rgb(220,2,0);border-radius:14px;}"
                table.horizontalHeader().setStyleSheet(stylesheet)
                # table.setItem(0, 0, QTableWidgetItem(location_country))
                # set data

                header = table.horizontalHeader()
                header.setResizeMode(QHeaderView.ResizeToContents)
                header.setStretchLastSection(True)
                # print(QtGui.QStyleFactory.keys())

                #separator = ' , '
                if text < '5':
                    table.setItem(0, 1, QTableWidgetItem("   Risk"))
                    table.setItem(0, 0, QTableWidgetItem(location_country.capitalize()))

                    table.setItem(0, 4, QTableWidgetItem(str(separator.join(str(element) for element in b1))))
                    table.setItem(0, 5, QTableWidgetItem((b3)))

                    table.horizontalHeaderItem(1).setToolTip("Warning! High Risk to send Tweet!!")
                    table.horizontalHeaderItem(2).setToolTip("Medium Risk")
                    table.horizontalHeaderItem(3).setToolTip("Low Risk to send Tweet!! ")
                    table.horizontalHeaderItem(4).setToolTip("Names of political parties mention in your tweet")
                    table.horizontalHeaderItem(5).setToolTip("DBpedia URL")


                elif '5' <= text < '7':
                    table.setItem(0, 2, QTableWidgetItem("Warn"))
                    table.setItem(0, 0, QTableWidgetItem(location_country.capitalize()))
                    #table.setItem(1, 0, QTableWidgetItem(b8.capitalize()))
                    table.setItem(0, 4, QTableWidgetItem(str(separator.join(str(element) for element in b1))))
                    table.setItem(0, 5, QTableWidgetItem(str(separator.join(str(element) for element in b2))))
                    table.horizontalHeaderItem(1).setToolTip("Warning! High Risk to send Tweet!!")
                    table.horizontalHeaderItem(2).setToolTip("Medium Risk")
                    table.horizontalHeaderItem(3).setToolTip("Low Risk to send Tweet!! ")
                    table.horizontalHeaderItem(4).setToolTip("Names of political parties mention in your tweet")
                    table.horizontalHeaderItem(5).setToolTip("DBpedia URL")

                elif text >= '7':
                    table.setItem(0, 3, QTableWidgetItem("  Safe"))
                    table.setItem(0, 0, QTableWidgetItem(location_country.capitalize()))
                    #table.setItem(1, 0, QTableWidgetItem(b8.capitalize()))
                    table.setItem(0, 4, QTableWidgetItem(str(separator.join(str(element) for element in b1))))
                    table.setItem(0, 5, QTableWidgetItem(str(separator.join(str(element) for element in b2))))
                    table.horizontalHeaderItem(1).setToolTip("Warning! High Risk to send Tweet!!")
                    table.horizontalHeaderItem(2).setToolTip("Medium Risk")
                    table.horizontalHeaderItem(3).setToolTip("Low Risk to send Tweet!! ")
                    table.horizontalHeaderItem(4).setToolTip("Names of political parties mention in your tweet")
                    table.horizontalHeaderItem(5).setToolTip("DBpedia URL")

                else:
                    return None

                if text1 < '5':
                    table.setItem(1, 1, QTableWidgetItem("   Risk"))

                    table.setItem(1, 0, QTableWidgetItem(b8.capitalize()))





                elif '5' <= text1 < '7':
                    table.setItem(1, 2, QTableWidgetItem("Warn"))

                    table.setItem(1, 0, QTableWidgetItem(b8.capitalize()))


                elif text1 >= '7':
                    table.setItem(1, 3, QTableWidgetItem("  Safe"))

                    table.setItem(1, 0, QTableWidgetItem(b8.capitalize()))


                else:
                    return None

                # show table
                window = QWidget()
                table.show()
                window.addAction(table)
                window.show()
                # Mytable.setItem(0, 4, QTableWidgetItem(b))



        return QtGui.QWidget.eventFilter(self, widget, event)




def main():
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main())