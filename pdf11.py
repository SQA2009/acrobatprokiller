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
            # Renderiza a página em alta resolução (2x para boa qualidade)
            page = self.current_document[self.current_page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)  # Ajuste do fator de escala

            # Verifica se os dados da imagem são válidos
            if not pix.samples:
                raise ValueError("Erro ao renderizar a página do PDF.")

            # Criação manual do QImage a partir dos bytes de pix.samples
            img = QImage(
                pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888
            )

            # Verifica se o QImage foi criado corretamente
            if img.isNull():
                raise ValueError("Erro ao criar QImage a partir dos dados renderizados.")

            # Converte QImage para NumPy array (garantindo compatibilidade)
            img_array = self.qimage_to_numpy(img)

            # Processa a imagem no "GPU"
            enhanced_img_array = self.gpu_process(img_array)

            # Reconverte para QImage após processamento
            enhanced_img = QImage(
                enhanced_img_array, enhanced_img_array.shape[1], enhanced_img_array.shape[0], QImage.Format_RGB888
            )

            # Adiciona a imagem processada à cena gráfica
            self.scene.clear()
            self.scene.addPixmap(QPixmap.fromImage(enhanced_img))

        except Exception as e:
            print(f"Erro ao renderizar página: {e}")

    def qimage_to_numpy(self, qimage):
        """Converte um QImage para NumPy array."""
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width, height = qimage.width(), qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())  # Garante que o ponteiro tenha o tamanho correto
        return np.array(ptr).reshape((height, width, 3))



    def gpu_process(self, img_array):
        """Simula processamento acelerado por GPU em uma matriz de imagem."""
        # Apenas converte para escala de cinza como exemplo
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
