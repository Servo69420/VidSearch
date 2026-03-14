

###HELL NO
print("To the moon!")
class Crypto:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def display_info(self):
        print(f"Cryptocurrency: {self.name} ({self.symbol})")

bitcoin = Crypto("Bitcoin", "BTC")
ethereum = Crypto("Ethereum", "ETH")
bitcoin.display_info()
ethereum.display_info()