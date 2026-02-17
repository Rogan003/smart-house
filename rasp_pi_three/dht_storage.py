class DHTStorage:
    def __init__(self):
        self.dht1_temp = 0
        self.dht1_hum = 0
        self.dht2_temp = 0
        self.dht2_hum = 0

    def update_dht1(self, temp, hum):
        self.dht1_temp = temp
        self.dht1_hum = hum

    def update_dht2(self, temp, hum):
        self.dht2_temp = temp
        self.dht2_hum = hum

    def get_dht1(self):
        return self.dht1_temp, self.dht1_hum

    def get_dht2(self):
        return self.dht2_temp, self.dht2_hum

dht_storage = DHTStorage()
