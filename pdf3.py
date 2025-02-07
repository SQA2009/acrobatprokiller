from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from OpenGL.GL import glClear, glViewport, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT

class OpenGLPDFViewer(QGLWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.scale = 1.0

    def load_page(self, image: QImage):
        """Load a page as an image to render."""
        self.image = image
        self.scale = 1.0
        self.update()

    def zoom(self, factor: float):
        """Apply zoom to the image."""
        self.scale *= factor
        self.update()

    def paintGL(self):
        """Render the content using OpenGL."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear the screen
        if self.image:
            img_data = self.image.scaled(
                self.image.width() * self.scale,
                self.image.height() * self.scale,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            pixmap = QPixmap.fromImage(img_data)
            self.renderPixmap(pixmap)

    def renderPixmap(self, pixmap):
        """Draw the QPixmap on the OpenGL widget."""
        self.makeCurrent()
        self.qglColor(Qt.white)
        self.drawTexture(self.rect(), pixmap)

    def resizeGL(self, w, h):
        """Adjust the OpenGL viewport when the widget is resized."""
        glViewport(0, 0, w, h)
