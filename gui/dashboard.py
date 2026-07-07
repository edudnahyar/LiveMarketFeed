from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

from PySide6.QtCore import QTimer

import redis

from gui.Widgets.marketcard import MarketCard


class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Market Cyberdeck"
        )

        self.resize(
            1200,
            700
        )


        # Redis connection

        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )


        # Layout

        main_layout = QVBoxLayout()


        title = QLabel(
            "GLOBAL MARKETS"
        )

        title.setStyleSheet(
            "font-size: 32px;"
        )

        main_layout.addWidget(title)


        cards_layout = QHBoxLayout()


        self.cards = {

            "SP500": MarketCard(
                "S&P 500"
            ),

            "ASX200": MarketCard(
                "ASX 200"
            ),

            "FTSE100": MarketCard(
                "FTSE 100"
            ),

            "HSI": MarketCard(
                "Hang Seng"
            ),

            "EUROSTOXX": MarketCard(
                "EUROSTOXX"
            ),

            "Crude Oil": MarketCard(
                "Crude Oil"
            ),

            "Natural Gas": MarketCard(
                "Natural Gas"
            ),

            "Gold": MarketCard(
                "Gold"
            )

        }


        for card in self.cards.values():

            cards_layout.addWidget(card)


        main_layout.addLayout(
            cards_layout
        )


        self.setLayout(
            main_layout
        )


        # Refresh GUI every 5 seconds

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.refresh
        )

        self.timer.start(
            5000
        )


    def refresh(self):

        redis_keys = {

            "SP500": "market:^GSPC",

            "ASX200": "market:^AXJO",

            "FTSE100": "market:^FTSE",

            "HSI": "market:^HSI",

            "EUROSTOXX" : "market:^STOXX50E",

            "Crude Oil": "market:CL=F",

            "Natural Gas": "market:NG=F",

            "Gold": "market:GC=F"

        }


        for name, key in redis_keys.items():

            data = self.redis.hgetall(
                key
            )

            self.cards[name].update_market(
                data
            )