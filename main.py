import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import httpx


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 620)
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
        self.regymeButton = QtWidgets.QPushButton(MainWindow)
        self.regymeButton.setGeometry(QtCore.QRect(15, 500, 150, 50))
        self.reset_pointButton = QtWidgets.QPushButton(MainWindow)
        self.reset_pointButton.setGeometry(QtCore.QRect(170, 500, 175, 50))

        font = QtGui.QFont('Arial', 14)
        self.addressLabel = QtWidgets.QLabel(MainWindow)
        self.addressLabel.setGeometry(QtCore.QRect(15, 560, 550, 50))
        self.addressLabel.setFont(font)
        self.addressLabel.setWordWrap(True)

        self.add_indexRadioButton = QtWidgets.QRadioButton(MainWindow)
        self.add_indexRadioButton.setGeometry(QtCore.QRect(350, 500, 130, 50))
        font = QtGui.QFont('Arial', 10)
        self.add_indexRadioButton.setFont(font)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.searchButton.setText("Искать")
        self.regymeButton.setText(f'Вид карты: Схема')
        self.reset_pointButton.setText('Сброс поискового результата')
        self.addressLabel.setText('Здесь будет адрес')
        self.add_indexRadioButton.setText('Приписать индекс')

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.searchButton.clicked.connect(self.search_address)
        self.regymeButton.clicked.connect(self.change_regyme)
        self.reset_pointButton.clicked.connect(self.resetPoint)
        self.add_indexRadioButton.clicked.connect(self.editAddress)
        self.map_types = ('map', 'sat', 'sat,skl')
        self.map_types_names = ['Схема', 'Спутник', 'Гибрид']
        self.current_map = 0
        self.address = dict()

        geocoder_request = "http://geocode-maps.yandex.ru/1.x/" \
                           "?apikey=40d1649f-0493-4b70-98ba-98533de7710b&" \
                           "geocode=Неаполь&format=json"

        response = httpx.get(geocoder_request)
        json_response = response.json()

        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_cords = toponym["Point"]["pos"]
        cords = toponym_cords.split()

        self.url = f"https://static-maps.yandex.ru/1.x/"
        self.map_params = {'ll': ','.join(cords), 'spn': '0.1,0.1', 'l': 'map'}
        self.map_file = "map.png"

        self.change_map()


    def change_map(self):
        response = httpx.get(self.url, params=self.map_params)
        with open(self.map_file, "wb") as file:
            file.write(response.content)
        self.pix = QtGui.QPixmap(self.map_file)
        self.label.setPixmap(self.pix)

    def change_regyme(self):
        self.current_map = (self.current_map + 1) % 3
        self.map_params['l'] = self.map_types[self.current_map]
        self.change_map()
        self.regymeButton.setText(f'Вид карты: {self.map_types_names[self.current_map]}')

    def resetPoint(self):
        del self.map_params['pt']
        self.addressLabel.setText('Здесь будет адрес')
        self.change_map()

    def search_address(self):
        geocoder_request = "http://geocode-maps.yandex.ru/1.x/" \
                           "?apikey=40d1649f-0493-4b70-98ba-98533de7710b&" \
                           f"geocode={self.inputWidget.text()}&format=json"
        response = httpx.get(geocoder_request)
        if response:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            self.address = toponym['metaDataProperty']['GeocoderMetaData']['Address']
            toponym_cords = toponym['Point']['pos'].replace(' ', ',')
            self.map_params['ll'] = toponym_cords
            self.map_params['spn'] = ','.join(get_auto_spn(toponym))
            self.map_params['pt'] = f'{toponym_cords},pm2rdm'
            self.change_map()

            self.addressLabel.setText(f"Адрес: {self.address['formatted']}")
            if self.add_indexRadioButton.isChecked() and 'postal_code' in self.address:
                self.addressLabel.setText(f"{self.addressLabel.text()} -- {self.address['postal_code']}")

    def editAddress(self):
        if self.address:
            if self.add_indexRadioButton.isChecked() and 'postal_code' in self.address:
                self.addressLabel.setText(f"Адрес: {self.address['formatted']} -- {self.address['postal_code']}")
            else:
                self.addressLabel.setText(f"Адрес: {self.address['formatted']}")

    def keyPressEvent(self, event):
        #  Изменение масштаба
        if event.key() == Qt.Key_PageUp:
            spn = map(lambda x: str(min(float(x) * 2, 10)), self.map_params['spn'].split(','))
            self.map_params['spn'] = ','.join(spn)
            self.change_map()
        elif event.key() == Qt.Key_PageDown:
            spn = map(lambda x: str(max(float(x) / 2, 0.01)), self.map_params['spn'].split(','))
            self.map_params['spn'] = ','.join(spn)
            self.change_map()
        #  Движение камеры
        elif event.key() == Qt.Key_Up:
            spn = float(self.map_params['spn'].split(',')[0])
            ll = self.map_params['ll'].split(',')
            ll[1] = str(min(float(ll[1]) + 0.5 * spn, 80))
            self.map_params['ll'] = ','.join(ll)
            self.change_map()
        elif event.key() == Qt.Key_Down:
            spn = float(self.map_params['spn'].split(',')[0])
            ll = self.map_params['ll'].split(',')
            ll[1] = str(max(float(ll[1]) - 0.5 * spn, -80))
            self.map_params['ll'] = ','.join(ll)
            self.change_map()
        elif event.key() == Qt.Key_Right:
            spn = float(self.map_params['spn'].split(',')[0])
            ll = self.map_params['ll'].split(',')
            ll[0] = str(min(float(ll[0]) + 0.5 * spn, 170))
            self.map_params['ll'] = ','.join(ll)
            self.change_map()
        elif event.key() == Qt.Key_Left:
            spn = float(self.map_params['spn'].split(',')[0])
            ll = self.map_params['ll'].split(',')
            ll[0] = str(max(float(ll[0]) - 0.5 * spn, -170))
            self.map_params['ll'] = ','.join(ll)
            self.change_map()

    def mousePressEvent(self, event):
        focused_widget = QtGui.QGuiApplication.focusObject()
        if isinstance(focused_widget, QtWidgets.QLineEdit):
            focused_widget.clearFocus()
        self.setFocus()


def get_auto_spn(obj: dict):
    frame = obj['boundedBy']['Envelope']
    lowerCorner = frame['lowerCorner']
    upperCorner = frame['upperCorner']
    left, bottom = lowerCorner.split()
    right, up = upperCorner.split()
    dx = abs(float(left) - float(right))
    dy = abs(float(up) - float(bottom))
    return str(dx), str(dy)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
