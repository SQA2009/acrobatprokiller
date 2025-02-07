import sys
import fitz  # PyMuPDF para leitura e manipulação de PDFs
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader com GPU Rendering")
        self.setGeometry(100, 100, 1200, 800)

        # Configuração principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Cena para exibição do PDF
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)

        # Botão para abrir PDF
        self.open_button = QPushButton("Abrir PDF")
        self.open_button.clicked.connect(self.open_pdf)
        self.layout.addWidget(self.open_button)

        # Variável para armazenar o documento atual
        self.pdf_document = None
        self.current_page_index = 0

    def open_pdf(self):
        # Selecionar arquivo PDF
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo PDF", "", "Arquivos PDF (*.pdf)")
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        # Abrir o PDF com fitz (PyMuPDF)
        self.pdf_document = fitz.open(file_path)
        self.current_page_index = 0
        self.display_page(self.current_page_index)

    def display_page(self, page_index):
        if not self.pdf_document:
            return

        # Obter a página
        page = self.pdf_document[page_index]
        pix = page.get_pixmap()  # Renderizar a página como imagem
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

        # Renderizar a imagem na cena
        self.scene.clear()
        pixmap = QPixmap.fromImage(image)
        self.scene.addPixmap(pixmap)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        # Navegação por teclas
        if not self.pdf_document:
            return

        if event.key() == Qt.Key_Right and self.current_page_index < len(self.pdf_document) - 1:
            self.current_page_index += 1
            self.display_page(self.current_page_index)

        elif event.key() == Qt.Key_Left and self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_page(self.current_page_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = PDFReader()
    reader.show()
    sys.exit(app.exec_())
