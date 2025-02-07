import sys
import fitz  # PyMuPDF para manipulação de PDFs
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QScrollArea, QLabel,
    QVBoxLayout, QSlider, QStatusBar, QLineEdit, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QImage, QPixmap, QIntValidator


class RenderPageThread(QThread):
    rendered = pyqtSignal(int, QPixmap)

    def __init__(self, document, page_number, zoom_factor):
        super().__init__()
        self.document = document
        self.page_number = page_number
        self.zoom_factor = zoom_factor

    def run(self):
        try:
            page = self.document[self.page_number]
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            self.rendered.emit(self.page_number, pixmap)
        except Exception as e:
            print(f"Error rendering page {self.page_number}: {e}")


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer")
        self.resize(1024, 768)

        self.current_document = None
        self.zoom_factor = 1.0
        self.page_spacing = 20
        self.page_widgets = []
        self.render_threads = []
        self.rendering_queue = []
        self.rendering_in_progress = set()
        self.render_mutex = QMutex()
        self.page_positions = []

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        # Content widget inside the scroll area
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(self.page_spacing)
        self.content_layout.setAlignment(Qt.AlignHCenter)

        # Background styling
        self.content_widget.setStyleSheet("background-color: rgba(231,236,241,255); border: none;")

        # Status bar for page number and zoom
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.page_label = QLabel("Page: -")
        self.status_bar.addWidget(self.page_label)

        # Zoom controls: slider and manual input
        self.zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setRange(10, 5000)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)

        self.zoom_input = QLineEdit("100", self)
        self.zoom_input.setFixedWidth(60)
        self.zoom_input.setValidator(QIntValidator(10, 5000))
        self.zoom_input.returnPressed.connect(self.on_zoom_input_changed)

        self.zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_layout.addWidget(self.zoom_slider)
        self.zoom_layout.addWidget(self.zoom_input)

        zoom_container = QWidget()
        zoom_container.setLayout(self.zoom_layout)
        self.status_bar.addPermanentWidget(zoom_container)

        # Menu
        self.init_menu()

        # Connect scroll changes to update the current page display
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.update_current_page)

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = file_menu.addAction("Open PDF")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_name:
            try:
                self.current_document = fitz.open(file_name)
            except Exception as e:
                print(f"Error opening PDF: {e}")
                return

            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            self.page_widgets.clear()
            self.render_threads.clear()
            self.zoom_factor = 1.0
            self.zoom_slider.setValue(100)
            self.zoom_input.setText("100")

            self.load_pages()

    def load_pages(self):
        if not self.current_document:
            return

        total_pages = len(self.current_document)
        self.page_positions = []

        for i in range(total_pages):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(label)
            self.page_widgets.append(label)

            position_marker = QLabel("")
            position_marker.setFixedHeight(1)
            position_marker.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(position_marker)

            self.page_positions.append(position_marker)

        self.page_label.setText(f"Page: 1/{total_pages}")
        self.queue_render_pages()

    def queue_render_pages(self):
        for i in range(len(self.page_widgets)):
            if i not in self.rendering_in_progress and i not in self.rendering_queue:
                self.rendering_queue.append(i)
        self.process_render_queue()

    def process_render_queue(self):
        self.render_mutex.lock()
        if self.rendering_queue and not self.rendering_in_progress:
            next_page = self.rendering_queue.pop(0)
            self.start_render_thread(next_page)
        self.render_mutex.unlock()

    def start_render_thread(self, page_number):
        if page_number not in self.rendering_in_progress:
            thread = RenderPageThread(self.current_document, page_number, self.zoom_factor)
            thread.rendered.connect(self.update_page_content)
            self.render_threads.append(thread)
            thread.start()
            self.rendering_in_progress.add(page_number)

    def update_page_content(self, page_number, pixmap):
        if 0 <= page_number < len(self.page_widgets):
            label = self.page_widgets[page_number]
            label.setPixmap(pixmap)

            if page_number in self.rendering_in_progress:
                self.rendering_in_progress.remove(page_number)

            self.process_render_queue()

    def update_current_page(self):
        if not self.page_positions:
            return

        scroll_center = (
            self.scroll_area.verticalScrollBar().value() + self.scroll_area.height() // 2
        )

        closest_page = 0
        closest_distance = float('inf')
        for i, marker in enumerate(self.page_positions):
            marker_pos = marker.y() + marker.height() // 2
            distance = abs(marker_pos - scroll_center)
            if distance < closest_distance:
                closest_distance = distance
                closest_page = i

        total_pages = len(self.page_positions)
        self.page_label.setText(f"Page: {closest_page + 1}/{total_pages}")

    def on_zoom_slider_changed(self, value):
        self.zoom_factor = value / 100.0
        self.zoom_input.setText(str(value))
        self.reload_pages_with_zoom()

    def on_zoom_input_changed(self):
        try:
            value = int(self.zoom_input.text())
            self.zoom_factor = value / 100.0
            self.zoom_slider.setValue(value)
            self.reload_pages_with_zoom()
        except ValueError:
            pass

    def reload_pages_with_zoom(self):
        self.rendering_in_progress.clear()
        self.rendering_queue.clear()
        self.queue_render_pages()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec_())
