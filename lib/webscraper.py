import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

'''
⏰ Schedule the Script
1. On Unix/Linux/macOS (Using cron)
    crontab -e
    0 * * * * /usr/bin/python3 /path/to/your/script.py
'''



station_ids = ['KA8YES', 'EN90_01', 'OE6ISP_2']  # Replace with actual IDs
base_url = 'https://tinygs.com/station/'
all_packets = []

for station_id in station_ids:
    url = f"{base_url}{station_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')  # TODO: Adjust selector based on actual HTML structure

    if table:
        rows = table.find_all('tr')[1:]  
        for row in rows:
            cols = row.find_all('td')
            packet_info = {
                'Station ID': station_id,
                'Timestamp': cols[0].text.strip(),
                'Satellite': cols[1].text.strip(),
                'Frequency': cols[2].text.strip(),
                'RSSI': cols[3].text.strip(),
                'SNR': cols[4].text.strip(),
                'Data': cols[5].text.strip()
            }
            all_packets.append(packet_info)

df = pd.DataFrame(all_packets)
df['Retrieved At'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

print(df)

csv_filename = 'pittsburgh_tinygs_packets.csv'
df.to_csv(csv_filename, index=False)