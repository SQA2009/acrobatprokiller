import sys
import fitz  # PyMuPDF for PDF handling
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
)
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt
from OpenGL.GL import (
    glClear, glViewport, GL_COLOR_BUFFER_BIT, GL_TEXTURE_2D, glEnable,
    glGenTextures, glBindTexture, glTexImage2D, glTexParameteri, GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER, GL_LINEAR, glBegin, glEnd, GL_QUADS, glTexCoord2f, glVertex2f,
    GL_RGBA, GL_UNSIGNED_BYTE
)


class OpenGLPDFViewer(QGLWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.texture_id = None

    def load_page(self, image: QImage):
        """Load a page as an image to render."""
        self.image = image
        self.update()

    def initializeGL(self):
        """Initialize OpenGL settings."""
        glEnable(GL_TEXTURE_2D)

def paintGL(self):
    """Render the current image using OpenGL."""
    glClear(GL_COLOR_BUFFER_BIT)

    if self.image:
        print("Image is loaded for rendering.")
        self.image = self.image.convertToFormat(QImage.Format_RGBA8888)
        width = self.image.width()
        height = self.image.height()
        raw_data = self.image.bits().asstring(width * height * 4)

        if not self.texture_id:
            self.texture_id = glGenTextures(1)
            print(f"Texture ID generated: {self.texture_id}")

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)
        print(f"Texture uploaded: {width}x{height}")

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Draw a textured quad
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
    else:
        print("No image loaded to render.")



    def resizeGL(self, w, h):
        """Adjust the viewport when the widget is resized."""
        glViewport(0, 0, w, h)


class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader with OpenGL")
        self.setGeometry(100, 100, 1200, 800)

        # State variables
        self.pdf_document = None
        self.current_page_index = 0

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # OpenGL Viewer
        self.opengl_viewer = OpenGLPDFViewer()
        self.layout.addWidget(self.opengl_viewer)

# Controls
controls_layout = QHBoxLayout()
self.open_button = QPushButton("Open PDF")
self.open_button.clicked.connect(self.open_pdf)
controls_layout.addWidget(self.open_button)

self.prev_button = QPushButton("Previous")
self.prev_button.clicked.connect(self.show_previous_page)  # Conecta ao método show_previous_page
controls_layout.addWidget(self.prev_button)

self.next_button = QPushButton("Next")
self.next_button.clicked.connect(self.show_next_page)  # Conecta ao método show_next_page
controls_layout.addWidget(self.next_button)

self.layout.addLayout(controls_layout)

    def open_pdf(self):
        """Open a PDF file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document = fitz.open(file_path)
            self.current_page_index = 0
            self.display_page(self.current_page_index)

def display_page(self, page_index):
    """Display a specific page."""
    if not self.pdf_document:
        return

    page = self.pdf_document[page_index]
    # Render the page at higher resolution (300 DPI)
    pix = page.get_pixmap(dpi=300)
    print(f"Page rendered: {pix.width}x{pix.height}")
    
    image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888)
    if image.isNull():
        print("Failed to create QImage")
    else:
        print(f"QImage created: {image.width()}x{image.height()}")
    
    self.opengl_viewer.load_page(image)

def show_next_page(self):
    """Show the next page."""
    if self.pdf_document and self.current_page_index < len(self.pdf_document) - 1:
        self.current_page_index += 1
        self.display_page(self.current_page_index)

def show_previous_page(self):
    """Show the previous page."""
    if self.pdf_document and self.current_page_index > 0:
        self.current_page_index -= 1
        self.display_page(self.current_page_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = PDFReader()
    reader.show()
    sys.exit(app.exec_())