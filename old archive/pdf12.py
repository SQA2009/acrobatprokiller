import sys
import fitz  # PyMuPDF para manipular PDFs
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

        # Defina o foco para que a janela principal receba os eventos de teclado
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
            
            # Verifique se o pixmap tem dados válidos
            if not pix.samples:
                raise ValueError("Erro ao renderizar a página: pix.samples está vazio ou inválido.")

            # Criação do QImage a partir do pixmap.samples
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            if img.isNull():
                raise ValueError("Erro ao criar QImage a partir dos dados renderizados.")

            # Convertemos o QImage para um array NumPy
            img_array = self.qimage_to_numpy(img)

            # Processa a imagem no "GPU"
            enhanced_img_array = self.gpu_process(img_array)

            # Reconversão do array NumPy para QImage
            enhanced_img = QImage(
                enhanced_img_array, pix.width, pix.height, QImage.Format_RGB888
            )

            # Exibe a imagem na cena gráfica
            self.scene.clear()
            self.scene.addPixmap(QPixmap.fromImage(enhanced_img))

        except Exception as e:
            print(f"Erro ao renderizar página: {e}")

    def gpu_process(self, img_array):
        """Simula processamento acelerado por GPU em uma matriz de imagem."""
        # Exemplo de processamento simples: converte para escala de cinza
        gray_image = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
        return np.repeat(gray_image[:, :, np.newaxis], 3, axis=2).astype(np.uint8)

    def next_page(self):
        if self.current_document and self.current_page_index < len(self.current_document) - 1:
            self.current_page_index += 1
            self.render_page()

    def previous_page(self):
        if self.current_document and self.current_page_index > 0:
            self.current_page_index -= 1
            self.render_page()

    def keyPressEvent(self, event):
        """Captura eventos de tecla e navega pelas páginas."""
        if event.key() == Qt.Key_S or event.key() == Qt.Key_D:
            # "Right Arrow" or "Down Arrow" moves to next page
            self.next_page()
        elif event.key() == Qt.Key_W or event.key() == Qt.Key_A:
            # "Left Arrow" or "Up Arrow" moves to previous page
            self.previous_page()
        elif event.key() == Qt.Key_Escape:
            # Escape key can be used to close the viewer
            self.close()

    def qimage_to_numpy(self, qimage):
        """Converte um QImage para um array NumPy."""
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width, height = qimage.width(), qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())  # Garante que o ponteiro tenha o tamanho correto
        return np.array(ptr).reshape((height, width, 3))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
