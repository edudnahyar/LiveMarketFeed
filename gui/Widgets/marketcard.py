from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MarketCard(QFrame):

    def __init__(self, title):
        super().__init__()

        self.title_label = QLabel(title)
        self.price_label = QLabel("--")
        self.change_label = QLabel("--")

        layout = QVBoxLayout()

        layout.addWidget(self.title_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.change_label)

        self.setLayout(layout)

        self.setStyleSheet("""
            QFrame {
                border: 2px solid #444;
                border-radius: 10px;
                padding: 15px;
            }

            QLabel {
                font-size: 20px;
            }
        """)


    def update_market(self, data):

        price = data.get("price", "--")
        change = data.get("change", "--")

        self.price_label.setText(
            f"{price}"
        )

        self.change_label.setText(
            f"{change}%"
        )