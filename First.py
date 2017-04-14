# -*- coding: utf-8 -*-
from PySide import QtGui
import sys
import spotlight
import xlrd
from urllib2 import urlopen
from contextlib import closing
reload(sys)
sys.setdefaultencoding('utf-8')
from PyQt4.QtGui import *
import re
from matplotlib.pylab import *
import tweepy
from PyQt4 import QtGui, QtCore
import json, ast
from PyQt4.QtGui import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QFrame, QGridLayout, QVBoxLayout,
)
from PyQt4.QtCore import *


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
        
        self.frame = QFrame(self)
        box = QtGui.QHBoxLayout()       
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

        CONSUMER_KEY = ''
        CONSUMER_SECRET = ''
        ACCESS_KEY = ''
        ACCESS_SECRET = ''

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

        api = tweepy.API(auth)
        
        self.statusBar().showMessage('Sending... ')
        api.update_status(status=tweet)
        self.statusBar().showMessage('Your Tweet was send ')
        self.textedit.clear()
        
    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return:
                with open("mix.txt")as f:
                    file = [line.strip() for line in f]
                tweet = self.textedit.toPlainText()
                tweets = str(tweet).split()          
                l = 0
                tweet_sentiment = sentiment(str(tweets))
                ts = float(tweet_sentiment)               
                norm_ts = (10) * ((float(ts) - (-5)) / (5 - (-5)))              
                list = [((0.25) * norm_ts)]
                for j in range(len(tweets)):
                    was = False
                    for i in range(len(file)):
                        if tweets[j] == file[i]:                         
                            words_sentiment = float(sentiment(tweets[j]))
                            norm_ws = (10) * ((float(words_sentiment) - (-5)) / (5 - (-5)))
                            l = l + 1
                            was = True
                            list.append(((0.25) * norm_ws) / 6)

                url = 'http://freegeoip.net/json/'
                try:
                    with closing(urlopen(url)) as response:
                        location = json.loads(response.read())
                        location_country = location['country_name']

                        #print location_country
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

                        Fotn = [i for n, (s, i) in enumerate(m) if s == location_country]
                        Fotn_index = str(Fotn).strip('[]')
                        norm = (-10) * ((float(Fotn_index) - 0) / 100) + 10
                        print "Fotn_index: " + str(Fotn_index)
                        print "norm: " + str(norm)
                        list.append((0.25) * float(norm))

                        Democracy = [i for n, (s, i) in enumerate(m2) if s == location_country]
                        Democracy_index = str(Democracy).strip('[]')
                        list.append((0.25) * float(Democracy_index))

                except:
                    print("error")

                annotations = spotlight.annotate('http://spotlight.sztaki.hu:2222/rest/annotate', str(tweet))
                d = ast.literal_eval(json.dumps(annotations))            
                size = 2
                h = filter(
                    lambda person: person[
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
                    list.append(sentiment(l['surfaceForm']))
                    m.append(l['surfaceForm']), m.append(l['URI'])
                b = [m[i:i + size] for i in range(0, len(m), size)]              
                b1 = [item[0] for item in b]
                b2 = [item[1] for item in b]
                b3 = str(separator.join(str(element) for element in b2))
                annotations1 = spotlight.annotate('http://spotlight.sztaki.hu:2222/rest/annotate', str(tweet))

                d1 = ast.literal_eval(json.dumps(annotations1))               
                size = 2
                h1 = filter(
                    lambda place: place[
                                      'types'] == "Schema:Place,DBpedia:Place,DBpedia:PopulatedPlace,Schema:Country,DBpedia:Country",
                    d1)

                m1 = []

                for l1 in h1:
                    m1.append(l1['surfaceForm']), m1.append(l1['URI'])
                b4 = [m1[i:i + size] for i in range(0, len(m1), size)]
                b5 = [item[0] for item in b4]
                Countries = map(str.lower, b5)
                print ("show all Countries : ") + str(Countries)

                b6 = []
                for x in Countries:
                    if x != str(location_country.lower()):
                        b6.append(x)

                Dupcountries = set(b6)
                print "show duplicate_countries :" + str(Dupcountries)
                b8 = str(separator.join(str(element) for element in Dupcountries))
                print "extract county :" + str(b8)               
                with open("mix.txt")as f:
                    file1 = [line.strip() for line in f]
                tweets1 = str(tweet).split()         
                p = 0
                tweet_sentiment1 = sentiment(str(tweet))
                ts1 = float(tweet_sentiment1)        
                norm_ts1 = (10) * ((float(ts1) - (-5)) / (5 - (-5)))        
                list1 = [((0.25) * norm_ts1)]
                for j in range(len(tweets1)):
                    was = False
                    for i in range(len(file1)):
                        if tweets1[j] == file1[i]:
                            words_sentiment1 = float(sentiment(tweets[j]))
                            norm_ws = (10) * ((float(words_sentiment1) - (-5)) / (5 - (-5)))                       
                            p = p + 1
                            was = True
                            list1.append(((0.25) * norm_ws1) / 6)
                            print p
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
                        m1 = ast.literal_eval(json.dumps(required_data11))
                        m21 = ast.literal_eval(json.dumps(required_data21))
                        m1.pop(0)
                        m21.pop(0)

                Fotn1 = [i for n, (s, i) in enumerate(m1) if s == b8.capitalize()]
                Fotn_index1 = str(Fotn1).strip('[]')
                norm1 = (-10) * ((float(Fotn_index1) - 0) / 100) + 10
                list1.append((0.25) * float(norm1))
                Democracy1 = [i for n, (s, i) in enumerate(m21) if s == b8.capitalize()]
                Democracy_index1 = str(Democracy1).strip('[]')
                list1.append((0.25) * float(Democracy_index1))
                text = (str(sum(list)))
                text1 = (str(sum(list1)))               
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
                header = table.horizontalHeader()
                header.setResizeMode(QHeaderView.ResizeToContents)
                header.setStretchLastSection(True)
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

        return QtGui.QWidget.eventFilter(self, widget, event)

def main():
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
