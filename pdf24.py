import sys
import fitz  # PyMuPDF for handling PDFs
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QScrollArea, QLabel,
    QVBoxLayout, QSlider, QStatusBar, QLineEdit, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QImage, QPixmap, QIntValidator


class RenderPageThread(QThread):
    # Signal for page rendering completion with the page number and pixmap
    rendered = pyqtSignal(int, QPixmap)

    def __init__(self, document, page_number, zoom_factor):
        super().__init__()
        self.document = document
        self.page_number = page_number
        self.zoom_factor = zoom_factor

    def run(self):
        try:
            print(f"Rendering page {self.page_number} at zoom {self.zoom_factor * 100:.0f}%")
            page = self.document[self.page_number]
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Convert to QPixmap
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            # Emit the signal with the page number and the rendered pixmap
            self.rendered.emit(self.page_number, pixmap)
            print(f"Finished rendering page {self.page_number}")
        except Exception as e:
            print(f"Error rendering page {self.page_number}: {e}")


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - Debug Mode")
        self.resize(1024, 768)

        # Initial configurations
        self.current_document = None
        self.zoom_factor = 1.0
        self.page_spacing = 20
        self.page_widgets = []  # Visible page widgets
        self.render_threads = []  # Active rendering threads
        self.rendering_queue = []  # Queue of pages to render
        self.rendering_in_progress = set()  # Track rendering pages
        self.render_mutex = QMutex()  # Mutex to synchronize rendering of pages

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
        self.content_widget.setStyleSheet(""" 
            background-color: rgba(231,236,241,255); 
            border: none; 
        """)

        # Status bar for page number and zoom
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.page_label = QLabel("Page: -")
        self.status_bar.addWidget(self.page_label)

        # Zoom controls: slider and manual input
        self.zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setRange(10, 5000)  # Zoom from 10% to 5000%
        self.zoom_slider.setValue(100)  # Default zoom: 100%
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

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = file_menu.addAction("Open PDF")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_name:
            print(f"Opening PDF file: {file_name}")
            try:
                self.current_document = fitz.open(file_name)
            except Exception as e:
                print(f"Error opening PDF: {e}")
                return

            # Clear existing layout and widgets
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Reset configurations
            self.page_widgets.clear()
            self.render_threads.clear()
            self.zoom_factor = 1.0
            self.zoom_slider.setValue(100)  # Reset zoom to 100%
            self.zoom_input.setText("100")

            # Create placeholders for pages
            self.load_pages()

    def load_pages(self):
        """Creates placeholders for all pages."""
        if not self.current_document:
            return

        total_pages = len(self.current_document)
        print(f"Total pages in document: {total_pages}")

        for i in range(total_pages):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(label)
            self.page_widgets.append(label)

        # Start rendering the first page immediately
        print("Rendering first page immediately (page 0)")
        self.queue_render_pages()

    def queue_render_pages(self):
        """Queue all pages for rendering."""
        # Avoid rendering the same page multiple times
        for i in range(len(self.page_widgets)):
            # Only add pages to the rendering queue if they are not already in progress
            if i not in self.rendering_in_progress and i not in self.rendering_queue:
                self.rendering_queue.append(i)

        # Start the rendering process if no page is rendering
        self.process_render_queue()

    def process_render_queue(self):
        """Process pages in the queue, rendering them one by one."""
        self.render_mutex.lock()  # Locking mutex to ensure only one thread is running at a time
        if self.rendering_queue and not self.rendering_in_progress:
            next_page = self.rendering_queue.pop(0)
            print(f"Rendering page {next_page} at zoom {self.zoom_factor * 100:.0f}%")
            self.start_render_thread(next_page)
        self.render_mutex.unlock()  # Unlock mutex after processing

    def start_render_thread(self, page_number):
        """Start the rendering thread for the given page number."""
        if page_number not in self.rendering_in_progress:
            thread = RenderPageThread(self.current_document, page_number, self.zoom_factor)
            thread.rendered.connect(self.update_page_content)
            self.render_threads.append(thread)
            thread.start()

            # Ensure we add the page to the rendering set before starting the thread
            self.rendering_in_progress.add(page_number)
        else:
            print(f"Rendering for page {page_number} is already in progress.")

    def update_page_content(self, page_number, pixmap):
        """Update the page content after it has been rendered."""
        if 0 <= page_number < len(self.page_widgets):
            label = self.page_widgets[page_number]
            label.setPixmap(pixmap)
            print(f"Updated content for page {page_number}")

            # After rendering this page, safely remove it from the rendering set
            if page_number in self.rendering_in_progress:
                self.rendering_in_progress.remove(page_number)

            # Process the next page in the queue
            self.process_render_queue()

    def on_zoom_slider_changed(self, value):
        """Handles zoom changes from the slider."""
        self.zoom_factor = value / 100.0
        self.zoom_input.setText(str(value))
        self.reload_pages_with_zoom()

    def on_zoom_input_changed(self):
        """Handles zoom changes from the input field."""
        try:
            value = int(self.zoom_input.text())
            self.zoom_factor = value / 100.0
            self.zoom_slider.setValue(value)
            self.reload_pages_with_zoom()
        except ValueError:
            pass  # Invalid input, ignore

    def reload_pages_with_zoom(self):
        """Reload all pages with the new zoom factor."""
        print(f"Reloading pages with new zoom factor: {self.zoom_factor * 100:.0f}%")
        self.rendering_in_progress.clear()  # Clear rendering in progress before re-rendering
        self.rendering_queue.clear()  # Clear the render queue
        self.queue_render_pages()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec_())
