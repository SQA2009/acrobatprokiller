import sys
import fitz  # PyMuPDF para manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QScrollArea, QLabel,
    QFrame, QWidget, QVBoxLayout, QSlider, QStatusBar
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer


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
        self.current_page_rendering = 0  # Página sendo renderizada (para renderização incremental)

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

        # Estilo do fundo
        self.content_widget.setStyleSheet("""
            background-color: rgba(231,236,241,255);
            border: none;
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
        self.zoom_slider.setRange(10, 400)  # Zoom entre 10% e 400%
        self.zoom_slider.setValue(100)  # Zoom inicial: 100%
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
            print(f"Abrindo arquivo PDF: {file_name}")
            self.current_document = fitz.open(file_name)
            self.page_cache.clear()  # Limpa o cache ao abrir um novo arquivo
            self.zoom_factor = 1.0
            self.zoom_slider.setValue(100)  # Redefine o zoom para 100%
            self.current_page_rendering = 0  # Reinicia o contador de renderização
            self.render_pages_incrementally()

    def render_pages_incrementally(self):
        """Renderiza as páginas uma por uma usando um timer."""
        if not self.current_document:
            print("Nenhum documento carregado.")
            return

        # Limpa o layout existente antes de renderizar
        if self.current_page_rendering == 0:
            print("Limpando layout atual...")
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            print(f"Renderizando {len(self.current_document)} páginas com zoom {self.zoom_factor:.2f}...")

        # Verificar quais páginas estão visíveis e renderizá-las
        self.render_visible_pages()

    def render_visible_pages(self):
        """Renderiza as páginas visíveis com base na área de rolagem."""
        if not self.current_document:
            return

        # Obter o número total de páginas
        total_pages = len(self.current_document)
        viewport_top = self.scroll_area.verticalScrollBar().value()
        viewport_bottom = viewport_top + self.scroll_area.height()

        # Verificar quais páginas estão visíveis
        for i in range(total_pages):
            page_height = self.get_page_height(i)
            page_top = i * (page_height + self.page_spacing)
            page_bottom = page_top + page_height

            if page_bottom >= viewport_top and page_top <= viewport_bottom:
                self.render_page_if_needed(i)

    def render_page_if_needed(self, page_number):
        """Renderiza a página se necessário, dependendo do cache e zoom."""
        # Usa o cache se a página já foi renderizada com o mesmo zoom
        if (page_number, self.zoom_factor) in self.page_cache:
            return  # Página já renderizada, não faz nada

        print(f"Renderizando página {page_number + 1} com zoom {self.zoom_factor:.2f}x...")

        page = self.current_document[page_number]
        pixmap = self.render_page(page)

        # Armazena a renderização no cache
        self.page_cache[(page_number, self.zoom_factor)] = pixmap

        # Cria e adiciona o widget para a página renderizada
        page_widget = self.create_page_widget(page_number, pixmap)
        self.content_layout.addWidget(page_widget)

    def get_page_height(self, page_number):
        """Calcula a altura de uma página, levando em conta o zoom."""
        page = self.current_document[page_number]
        matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.height

    def create_page_widget(self, page_number, pixmap):
        """Cria um widget para exibir uma única página."""
        page_frame = QFrame()
        page_frame.setStyleSheet("background-color: white; border: 1px solid rgba(229,229,229,255);")
        page_frame_layout = QVBoxLayout(page_frame)
        page_frame_layout.setContentsMargins(0, 0, 0, 0)
        page_frame_layout.setAlignment(Qt.AlignCenter)

        label = QLabel()
        label.setPixmap(pixmap)
        page_frame_layout.addWidget(label)

        return page_frame

    def render_page(self, page):
        """Renderiza uma única página e retorna um QPixmap."""
        try:
            # Atualiza o zoom baseado no zoom_factor
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Cria um QImage a partir dos dados da página renderizada
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            if img.isNull():
                raise ValueError("Erro ao criar a imagem a partir dos dados renderizados.")

            print(f"Página renderizada: {pix.width}x{pix.height} pixels.")
            return QPixmap.fromImage(img)

        except Exception as e:
            print(f"Erro ao renderizar página: {e}")
            raise

    def update_zoom(self):
        """Atualiza o nível de zoom e redesenha as páginas."""
        zoom_percent = self.zoom_slider.value()
        self.zoom_factor = zoom_percent / 100.0  # Converte para um fator (1.0 = 100%)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
        print(f"Zoom atualizado para {zoom_percent}% ({self.zoom_factor:.2f}x)")

        # Limpar o cache e renderizar novamente as páginas visíveis
        self.page_cache.clear()
        self.render_pages_incrementally()

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

        total_pages = len(self.current_document) if self.current_document else 0
        self.page_label.setText(f"Página: {current_page} de {total_pages}")
        print(f"Página atual: {current_page}/{total_pages}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
