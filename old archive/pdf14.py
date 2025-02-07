import sys
import fitz  # PyMuPDF para manipulação de PDFs
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QFileDialog,
    QVBoxLayout, QWidget, QLabel, QSlider, QHBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - Zoom e Rolagem Contínuos")
        self.resize(1024, 768)

        # Configurações iniciais
        self.current_document = None
        self.current_page_index = 0
        self.zoom_factor = 1.0  # Fator de zoom inicial
        self.max_zoom_factor = 64.0  # Zoom máximo (6400%)
        self.min_zoom_factor = 0.25  # Zoom mínimo (25%)

        # Cache para páginas renderizadas
        self.page_cache = {}

        # Layouts e widgets
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.layout.addWidget(self.view)

        # Barra de informações
        self.info_bar = QHBoxLayout()
        self.page_label = QLabel("Página: 0/0")
        self.zoom_label = QLabel("Zoom: 100%")
        self.info_bar.addWidget(self.page_label)
        self.info_bar.addWidget(self.zoom_label)
        self.layout.addLayout(self.info_bar)

        # Slider de zoom
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(int(self.min_zoom_factor * 100))
        self.zoom_slider.setMaximum(int(self.max_zoom_factor * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(self.slider_zoom_changed)
        self.layout.addWidget(self.zoom_slider)

        # Menu
        self.init_menu()

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Arquivo")
        
        open_action = file_menu.addAction("Abrir PDF (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)

        first_page_action = file_menu.addAction("Primeira Página (Ctrl+Q)")
        first_page_action.setShortcut("Ctrl+Q")
        first_page_action.triggered.connect(self.go_to_first_page)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "Arquivos PDF (*.pdf)")
        if file_name:
            self.current_document = fitz.open(file_name)
            self.current_page_index = 0
            self.page_cache.clear()  # Limpa o cache ao abrir um novo arquivo
            self.render_pages()

    def render_pages(self):
        """Renderiza a página atual e armazena no cache."""
        if not self.current_document:
            return

        try:
            # Limpa a cena antes de renderizar novas páginas
            self.scene.clear()

            # Renderiza a página atual
            page = self.current_document[self.current_page_index]
            if self.current_page_index not in self.page_cache:
                self.page_cache[self.current_page_index] = self.render_page(page)

            pixmap = self.page_cache[self.current_page_index]
            self.scene.addPixmap(pixmap)

            # Ajusta a cena e as informações
            self.update_info_bar()
            self.view.setScene(self.scene)

        except Exception as e:
            print(f"Erro ao renderizar as páginas: {e}")

    def render_page(self, page):
        """Renderiza uma única página e retorna um QPixmap."""
        matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Cria um QImage a partir dos dados da página renderizada
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        if img.isNull():
            raise ValueError("Erro ao criar a imagem a partir dos dados renderizados.")

        return QPixmap.fromImage(img)

    def update_info_bar(self):
        """Atualiza os indicadores de página e zoom."""
        total_pages = len(self.current_document) if self.current_document else 0
        current_page = self.current_page_index + 1
        self.page_label.setText(f"Página: {current_page}/{total_pages}")
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")

    def slider_zoom_changed(self):
        """Atualiza o zoom com base na posição do slider."""
        self.zoom_factor = self.zoom_slider.value() / 100.0
        self.page_cache.clear()  # Limpa o cache para aplicar o novo zoom
        self.render_pages()

    def go_to_first_page(self):
        """Vai para a primeira página do documento."""
        if self.current_document:
            self.current_page_index = 0
            self.render_pages()

    def wheelEvent(self, event):
        """Navegação pelas páginas usando o scroll do mouse."""
        if event.angleDelta().y() < 0:  # Scroll para baixo: próxima página
            self.next_page()
        else:  # Scroll para cima: página anterior
            self.previous_page()

    def next_page(self):
        """Vai para a próxima página."""
        if self.current_document and self.current_page_index < len(self.current_document) - 1:
            self.current_page_index += 1
            self.render_pages()

    def previous_page(self):
        """Vai para a página anterior."""
        if self.current_document and self.current_page_index > 0:
            self.current_page_index -= 1
            self.render_pages()

    def keyPressEvent(self, event):
        """Captura os eventos de teclado para navegação entre páginas."""
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_D:
            # Próxima página
            self.next_page()
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_A:
            # Página anterior
            self.previous_page()
        elif event.key() == Qt.Key_Escape:
            # A tecla Escape fecha o visualizador
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
