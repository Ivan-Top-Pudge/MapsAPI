import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import requests


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 450)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(0, 50, 650, 450))
        self.label.setText("")
        self.label.setObjectName("label")

        self.inputWidget = QtWidgets.QLineEdit(MainWindow)
        self.inputWidget.setGeometry(QtCore.QRect(25, 0, 375, 50))

        self.searchButton = QtWidgets.QPushButton(MainWindow)
        self.searchButton.setGeometry(QtCore.QRect(425, 0, 150, 50))


        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.searchButton.setText("Искать")

class MyWidget(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        geocoder_request = "http://geocode-maps.yandex.ru/1.x/" \
                           "?apikey=40d1649f-0493-4b70-98ba-98533de7710b&" \
                           "geocode=Австралия&format=json"

        response = requests.get(geocoder_request)
        if response:
            json_response = response.json()

            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_cords = toponym["Point"]["pos"]
            cords = toponym_cords.split()

            map_request = f"https://static-maps.yandex.ru/1.x/?ll={cords[0]},{cords[1]}&spn=35,35&l=sat"
            response = requests.get(map_request)

        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        self.pix = QtGui.QPixmap('map.png')
        self.label.setPixmap(self.pix)
        self.searchButton.clicked.connect(self.search_address)

    def search_address(self):
        geocoder_request = "http://geocode-maps.yandex.ru/1.x/" \
                           "?apikey=40d1649f-0493-4b70-98ba-98533de7710b&" \
                           f"geocode={self.inputWidget.text()}&format=json"
        response = requests.get(geocoder_request)
        if response:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_cords = toponym['Point']['pos'].replace(' ', ',')

            map_request = f"https://static-maps.yandex.ru/1.x/?ll={toponym_cords}&spn=1,1&l=map&pt={toponym_cords},pm2rdm"
            response = requests.get(map_request)
            map_file = "map.png"
            with open(map_file, "wb") as file:
                file.write(response.content)
            self.pix = QtGui.QPixmap('map.png')
            self.label.setPixmap(self.pix)
            self.searchButton.clicked.connect(self.search_address)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec_())
