# Smart House

## Authors
Veselin Roganović SV36/2022

Tamara Cvjetković SV48/2022

## Short description
University IoT smart house project developed for Raspberry Pi.
[Specification](https://docs.google.com/document/d/1mjUrUa34hEqsPsrrYezyfnJUy_rae57oqkQ_S2_vkME) (in Serbian)

---

## Kako pokrenuti projekat

### 1. Pokretanje infrastrukture (Docker)

Prvo pokrenuti Docker kontejnere za MQTT Broker, InfluxDB i Grafanu:

```bash
cd infrastructure
docker-compose up -d
```

Ovo će pokrenuti:
- **MQTT Broker (Mosquitto)** - port `1883`
- **InfluxDB** - port `8086`
- **Grafana** - port `3000`

### 2. Pokretanje Flask servera

U novom terminalu:

```bash
cd server
pip install -r ../requirements.txt
python server.py
```

Server će raditi na `http://localhost:5000`

### 3. Pokretanje React Web aplikacije

U novom terminalu:

```bash
cd webapp
npm install
npm start
```

Web aplikacija će se otvoriti na `http://localhost:3001` (ili 3000 ako je slobodan)

### 4. Pokretanje PI skripti (simulatori)

U zasebnim terminalima za svaki PI:

```bash
# PI1
cd rasp_pi_one
pip install -r requirements.txt
python main.py

# PI2
cd rasp_pi_two
pip install -r requirements.txt
python main.py

# PI3
cd rasp_pi_three
pip install -r requirements.txt
python main.py
```

---

## Pristup servisima

| Servis | URL | Kredencijali |
|--------|-----|--------------|
| **Grafana** | http://localhost:3000 | admin / admin_password |
| **InfluxDB** | http://localhost:8086 | admin / adminadmin |
| **Flask API** | http://localhost:5000 | - |
| **React Web App** | http://localhost:3001 | - |

---

## Grafana Dashboard

Nakon pokretanja infrastrukture, Grafana je dostupna na:
- **URL:** http://localhost:3000
- **Username:** admin
- **Password:** admin_password

Dashboard sa svim senzorima se automatski učitava iz `infrastructure/grafana/provisioning/dashboards/`

---

## API Endpoints

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/status` | GET | Trenutno stanje sistema |
| `/alarm/deactivate` | POST | Isključi alarm |
| `/system/activate` | POST | Aktiviraj sigurnosni sistem |
| `/system/deactivate` | POST | Deaktiviraj sigurnosni sistem |
| `/timer/set` | POST | Postavi vrijeme štoperice |
| `/timer/configure` | POST | Konfiguriši N sekundi za BTN |
| `/timer/stop` | POST | Zaustavi treperenje |
| `/rgb/on` | POST | Uključi RGB sijalicu |
| `/rgb/off` | POST | Isključi RGB sijalicu |
| `/rgb/color` | POST | Postavi boju RGB sijalice |
| `/people/count` | GET | Broj osoba u objektu |