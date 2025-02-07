import sys
import fitz  # PyMuPDF para leitura e manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout, QSlider
)
from PyQt5.QtGui import QImage, QPixmap, QOpenGLWindow
from PyQt5.QtCore import Qt
from PyQt5.QtOpenGL import QGL, QGLWidget


class OpenGLPDFViewer(QGLWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.scale = 1.0

    def load_page(self, image: QImage):
        """Carrega uma página como imagem para ser renderizada."""
        self.image = image
        self.scale = 1.0
        self.update()

    def zoom(self, factor: float):
        """Aplica o zoom na imagem."""
        self.scale *= factor
        self.update()

    def paintGL(self):
        """Renderiza o conteúdo na GPU."""
        self.qglClearColor(Qt.white)  # Limpa o contexto com cor branca
        self.glClear(self.GL_COLOR_BUFFER_BIT | self.GL_DEPTH_BUFFER_BIT)

        if self.image:
            img_data = self.image.scaled(
                self.image.width() * self.scale,
                self.image.height() * self.scale,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            pixmap = QPixmap.fromImage(img_data)
            self.renderPixmap(pixmap)

    def renderPixmap(self, pixmap):
        """Desenha o QPixmap na área OpenGL."""
        self.makeCurrent()
        self.qglColor(Qt.white)
        self.drawTexture(self.rect(), pixmap)

    def resizeGL(self, w, h):
        """Redimensiona a janela OpenGL."""
        self.glViewport(0, 0, w, h)


class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader com OpenGL")
        self.setGeometry(100, 100, 1200, 800)

        # Variáveis de estado
        self.pdf_document = None
        self.current_page_index = 0

        # Configuração da GUI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Visualizador OpenGL
        self.opengl_viewer = OpenGLPDFViewer()
        self.layout.addWidget(self.opengl_viewer)

        # Controles de navegação
        controls_layout = QHBoxLayout()
        self.open_button = QPushButton("Abrir PDF")
        self.open_button.clicked.connect(self.open_pdf)
        controls_layout.addWidget(self.open_button)

        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_in_button.clicked.connect(lambda: self.opengl_viewer.zoom(1.2))
        controls_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom -")
        self.zoom_out_button.clicked.connect(lambda: self.opengl_viewer.zoom(0.8))
        controls_layout.addWidget(self.zoom_out_button)

        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.show_previous_page)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Próxima")
        self.next_button.clicked.connect(self.show_next_page)
        controls_layout.addWidget(self.next_button)

        self.layout.addLayout(controls_layout)

    def open_pdf(self):
        """Abre um arquivo PDF e carrega a primeira página."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo PDF", "", "Arquivos PDF (*.pdf)")
        if file_path:
            self.pdf_document = fitz.open(file_path)
            self.current_page_index = 0
            self.display_page(self.current_page_index)

    def display_page(self, page_index):
        """Exibe uma página específica do PDF."""
        if not self.pdf_document:
            return

        page = self.pdf_document[page_index]
        pix = page.get_pixmap()
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        self.opengl_viewer.load_page(image)

    def show_next_page(self):
        """Mostra a próxima página do PDF."""
        if self.pdf_document and self.current_page_index < len(self.pdf_document) - 1:
            self.current_page_index += 1
            self.display_page(self.current_page_index)

    def show_previous_page(self):
        """Mostra a página anterior do PDF."""
        if self.pdf_document and self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_page(self.current_page_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = PDFReader()
    reader.show()
    sys.exit(app.exec_())
