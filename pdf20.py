import sys
import fitz  # PyMuPDF para manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QScrollArea, QLabel,
    QVBoxLayout, QSlider, QStatusBar, QLineEdit, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QImage, QPixmap


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
        self.content_layout.setAlignment(Qt.AlignHCenter)  # Centraliza horizontalmente as páginas

        # Estilo do fundo
        self.content_widget.setStyleSheet("""
            background-color: rgba(231,236,241,255);
            border: none;
        """)

        # Barra de status para número da página e zoom
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.page_label = QLabel("Página: -")
        self.status_bar.addWidget(self.page_label)

        # Campo de zoom com slider e entrada manual
        self.zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setRange(10, 5000)  # Zoom entre 10% e 5000%
        self.zoom_slider.setValue(100)  # Zoom inicial: 100%
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)

        self.zoom_input = QLineEdit("100", self)
        self.zoom_input.setFixedWidth(60)
        self.zoom_input.setValidator(QIntValidator(10, 5000, self.zoom_input))
        self.zoom_input.returnPressed.connect(self.on_zoom_input_changed)

        self.zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_layout.addWidget(self.zoom_slider)
        self.zoom_layout.addWidget(self.zoom_input)

        zoom_container = QWidget()
        zoom_container.setLayout(self.zoom_layout)
        self.status_bar.addPermanentWidget(zoom_container)

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
            try:
                self.current_document = fitz.open(file_name)
            except Exception as e:
                print(f"Erro ao abrir PDF: {e}")
                return

            # Limpa o layout existente antes de carregar o novo PDF
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Limpa o cache e reinicia configurações
            self.page_cache.clear()
            self.zoom_factor = 1.0
            self.zoom_slider.setValue(100)  # Redefine o zoom para 100%
            self.zoom_input.setText("100")

            # Renderiza as páginas
            self.render_visible_pages()

    def render_visible_pages(self):
        """Renderiza apenas as páginas visíveis."""
        if not self.current_document:
            print("Nenhum documento carregado.")
            return

        # Pega o topo da área visível no scroll
        viewport_top = self.scroll_area.verticalScrollBar().value()
        viewport_bottom = viewport_top + self.scroll_area.height()

        total_pages = len(self.current_document)
        print(f"Renderizando páginas visíveis com zoom {self.zoom_factor:.2f}x...")

        for i in range(total_pages):
            page_height = self.get_page_height(i)
            page_top = i * (page_height + self.page_spacing)
            page_bottom = page_top + page_height

            if page_bottom >= viewport_top and page_top <= viewport_bottom:
                self.render_page(i)

    def render_page(self, page_number):
        """Renderiza uma página específica e adiciona ao layout."""
        if (page_number, self.zoom_factor) in self.page_cache:
            return  # Página já renderizada

        print(f"Renderizando página {page_number + 1} com zoom {self.zoom_factor:.2f}x...")

        page = self.current_document[page_number]
        pixmap = self.create_pixmap(page)

        # Armazena no cache
        self.page_cache[(page_number, self.zoom_factor)] = pixmap

        # Remove margens adicionais
        page_widget = self.create_page_widget(pixmap)
        self.content_layout.addWidget(page_widget)
        self.content_layout.setAlignment(Qt.AlignHCenter)  # Centraliza horizontalmente

    def create_page_widget(self, pixmap):
        """Cria um widget para exibir uma única página sem margens extras."""
        label = QLabel()
        label.setPixmap(pixmap)

        # Garante que o QLabel tenha o tamanho exato da imagem
        label.setFixedSize(pixmap.size())
        label.setAlignment(Qt.AlignCenter)

        # Adiciona o QLabel diretamente
        return label

    def create_pixmap(self, page):
        """Renderiza uma página do documento e retorna um QPixmap."""
        try:
            # Ajusta matriz de zoom sem rotação extra
            zoom_x = self.zoom_factor
            zoom_y = self.zoom_factor
            matrix = fitz.Matrix(zoom_x, zoom_y)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Debug: Exibe dimensões do PDF
            print(f"Página renderizada: {pix.width}x{pix.height} pixels (zoom {self.zoom_factor:.2f})")
            
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            if img.isNull():
                raise ValueError("Erro ao criar a imagem a partir dos dados renderizados.")
            return QPixmap.fromImage(img)
        except Exception as e:
            print(f"Erro ao renderizar página: {e}")
            raise

    def get_page_height(self, page_number):
        """Calcula a altura de uma página com base no zoom."""
        page = self.current_document[page_number]
        matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.height

    def on_zoom_slider_changed(self):
        """Dispara ao alterar o slider de zoom."""
        zoom_percent = self.zoom_slider.value()
        self.zoom_factor = zoom_percent / 100.0
        self.zoom_input.setText(str(zoom_percent))
        self.render_visible_pages()

    def on_zoom_input_changed(self):
        """Dispara ao inserir um valor manualmente no campo de zoom."""
        try:
            zoom_percent = int(self.zoom_input.text())
            if 10 <= zoom_percent <= 5000:
                self.zoom_slider.setValue(zoom_percent)  # Atualiza o slider
                self.zoom_factor = zoom_percent / 100.0
                self.render_visible_pages()
            else:
                print("Zoom fora dos limites (10% a 5000%)")
        except ValueError:
            print("Valor inválido para zoom")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec_())
