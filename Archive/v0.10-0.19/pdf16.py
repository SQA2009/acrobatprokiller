import sys
import fitz  # PyMuPDF para manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QFileDialog,
    QScrollArea, QLabel, QFrame, QWidget, QVBoxLayout, QSlider, QStatusBar, QStyle, QStyleOption
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt


class CustomScrollBar(QScrollArea):
    """ScrollBar personalizada para replicar o estilo do Windows 11."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - Fluent Design")
        self.resize(1024, 768)

        # Configurações iniciais
        self.current_document = None
        self.zoom_factor = 1.0
        self.page_spacing = 20  # Espaçamento entre páginas
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

        # Estilo do fundo e barras de rolagem
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: rgba(231,236,241,255);
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 16px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(80, 80, 80, 255);
                border-radius: 8px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(60, 60, 60, 255);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: rgba(200,200,200,255);
                border-radius: 4px;
                width: 14px;
                height: 14px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                subcontrol-position: bottom;
            }
            QScrollBar::sub-line:vertical {
                subcontrol-position: top;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 16px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(80, 80, 80, 255);
                border-radius: 8px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(60, 60, 60, 255);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: rgba(200,200,200,255);
                border-radius: 4px;
                width: 14px;
                height: 14px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:horizontal {
                subcontrol-position: right;
            }
            QScrollBar::sub-line:horizontal {
                subcontrol-position: left;
            }
        """)

        # Barra de status para número da página e zoom
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.page_label = QLabel("Página: -")
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addWidget(self.page_label)
        self.status_bar.addPermanentWidget(self.zoom_label)

        # Slider de zoom
        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setRange(1, 64)  # Zoom entre 100% e 6400%
        self.zoom_slider.setValue(10)  # Zoom inicial: 100%
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        self.status_bar.addPermanentWidget(self.zoom_slider)

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
            self.zoom_factor = 1.0
            self.zoom_slider.setValue(10)  # Redefine o zoom
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

            # Atualiza informações de status
            self.update_page_status()

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

    def update_zoom(self):
        """Atualiza o nível de zoom e redesenha as páginas."""
        self.zoom_factor = self.zoom_slider.value() / 10  # Slider 10 equivale a zoom 1.0 (100%)
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")
        self.render_pages()

    def wheelEvent(self, event):
        """Rolagem vertical suave."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - 30
            )
        else:
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() + 30
            )
        self.update_page_status()

    def keyPressEvent(self, event):
        """Atalhos de teclado para controle."""
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:  # "+" ou "="
            self.zoom_slider.setValue(self.zoom_slider.value() + 1)
        elif event.key() == Qt.Key_Minus:  # "-"
            self.zoom_slider.setValue(self.zoom_slider.value() - 1)
        elif event.key() == Qt.Key_Escape:
            self.close()

    def update_page_status(self):
        """Atualiza o rótulo do número da página."""
        viewport_top = self.scroll_area.verticalScrollBar().value()
        current_page = 1
        accumulated_height = 0

        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            accumulated_height += widget.height() + self.page_spacing
            if viewport_top < accumulated_height:
                current_page = i + 1
                break

        self.page_label.setText(f"Página: {current_page} de {len(self.current_document)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
