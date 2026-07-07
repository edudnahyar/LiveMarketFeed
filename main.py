import sys
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from services.market_services import run
from gui.app import app

# Directory

# Data Collection Layer
    # Indicies
        # S&P500
        # ASX200
        # STOXX50
        # FTSE100
        # HSI
    # Commodities
        # Oil
        # Gold
# Database Layer
    # Redis for live updates
    # Mongodb for saving documents
# UI Layer
    #Qt/QML
# Configuration Layer
    #YAML
class MarketWorker(QThread):
    def run(self):
        run()


def main():
    worker = MarketWorker()
    worker.start()

    app()

if __name__ == '__main__':
    main()


