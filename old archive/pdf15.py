import sys
import fitz  # PyMuPDF para manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QFileDialog,
    QGraphicsPixmapItem, QVBoxLayout, QScrollArea, QLabel, QFrame, QWidget
)
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtCore import Qt


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - Visualização Contínua")
        self.resize(1024, 768)

        # Configurações iniciais
        self.current_document = None
        self.zoom_factor = 1.0
        self.page_spacing = 20  # Espaçamento entre as páginas
        self.page_cache = {}

        # Área de rolagem
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        # Widget de conteúdo
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(self.page_spacing)
        self.content_layout.setAlignment(Qt.AlignHCenter)

        # Fundo do widget principal
        self.scroll_area.setStyleSheet("background-color: rgba(231,236,241,255);")

        # Menu
        self.init_menu()

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Arquivo")

        open_action = file_menu.addAction("Abrir PDF")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "Arquivos PDF (*.pdf)")
        if file_name:
            self.current_document = fitz.open(file_name)
            self.page_cache.clear()  # Limpa o cache ao abrir um novo arquivo
            self.render_pages()

    def render_pages(self):
        """Renderiza todas as páginas visíveis no layout."""
        if not self.current_document:
            return

        # Limpa o layout existente
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        try:
            # Adiciona cada página ao layout
            for page_number in range(len(self.current_document)):
                page_widget = self.create_page_widget(page_number)
                self.content_layout.addWidget(page_widget)

        except Exception as e:
            print(f"Erro ao renderizar páginas: {e}")

    def create_page_widget(self, page_number):
        """Cria um widget para exibir uma única página."""
        if page_number not in self.page_cache:
            # Renderiza a página se não estiver no cache
            page = self.current_document[page_number]
            pixmap = self.render_page(page)
            self.page_cache[page_number] = pixmap
        else:
            pixmap = self.page_cache[page_number]

        # Cria o widget da página
        page_frame = QFrame()
        page_frame.setStyleSheet("background-color: white; border: 1px solid rgba(229,229,229,255);")
        page_frame_layout = QVBoxLayout(page_frame)
        page_frame_layout.setContentsMargins(0, 0, 0, 0)
        page_frame_layout.setAlignment(Qt.AlignCenter)

        label = QLabel()
        label.setPixmap(self.page_cache[page_number])
        page_frame_layout.addWidget(label)

        return page_frame

    def render_page(self, page):
        """Renderiza uma única página e retorna um QPixmap."""
        matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Cria um QImage a partir dos dados da página renderizada
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        if img.isNull():
            raise ValueError("Erro ao criar a imagem a partir dos dados renderizados.")

        return QPixmap.fromImage(img)

    def wheelEvent(self, event):
        """Navegação suave com o scroll do mouse."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - 30
            )
        else:
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() + 30
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
