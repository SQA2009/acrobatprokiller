import sys
import fitz  # PyMuPDF for PDF manipulation
import numpy as np
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - GPU Accelerated")
        self.resize(1024, 768)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.current_document = None
        self.current_page_index = 0

        # Ensure the main window receives keyboard events
        self.view.setFocus()

        self.init_menu()

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        
        open_action = file_menu.addAction("Open PDF")
        open_action.triggered.connect(self.open_pdf)

        next_action = file_menu.addAction("Next Page")
        next_action.triggered.connect(self.next_page)

        prev_action = file_menu.addAction("Previous Page")
        prev_action.triggered.connect(self.previous_page)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.current_document = fitz.open(file_name)
            self.current_page_index = 0
            self.render_page()

    def render_page(self):
        if not self.current_document:
            return

        try:
            page = self.current_document[self.current_page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            
            # Ensure pix.samples has valid data
            if not pix.samples:
                raise ValueError("Error rendering page: pix.samples is empty or invalid.")

            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            if img.isNull():
                raise ValueError("Error creating QImage from rendered data.")

            img_array = self.qimage_to_numpy(img)

            # Preserve colors in the GPU process step
            enhanced_img_array = self.gpu_process(img_array)

            enhanced_img = QImage(
                enhanced_img_array, pix.width, pix.height, QImage.Format_RGB888
            )

            # Display the image in the graphics scene
            self.scene.clear()
            self.scene.addPixmap(QPixmap.fromImage(enhanced_img))

        except Exception as e:
            print(f"Error rendering page: {e}")

    def gpu_process(self, img_array):
        """Optional processing on the image array (preserves colors)."""
        # Simply return the original image array to preserve colors
        return img_array

    def next_page(self):
        if self.current_document and self.current_page_index < len(self.current_document) - 1:
            self.current_page_index += 1
            self.render_page()

    def previous_page(self):
        if self.current_document and self.current_page_index > 0:
            self.current_page_index -= 1
            self.render_page()

    def keyPressEvent(self, event):
        """Captures keyboard events and navigates pages with WSAD keys."""
        if event.key() == Qt.Key_D or event.key() == Qt.Key_S:
            # "D" or "S" moves to the next page
            self.next_page()
        elif event.key() == Qt.Key_A or event.key() == Qt.Key_W:
            # "A" or "W" moves to the previous page
            self.previous_page()
        elif event.key() == Qt.Key_Escape:
            # Escape key closes the viewer
            self.close()

    def qimage_to_numpy(self, qimage):
        """Converts a QImage to a NumPy array."""
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width, height = qimage.width(), qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        return np.array(ptr).reshape((height, width, 3))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
